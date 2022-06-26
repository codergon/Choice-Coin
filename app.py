import functools
import secrets

import sqlalchemy
from algosdk import constants, encoding
from algosdk.v2client import algod, indexer
from decouple import config
from marshmallow import Schema, fields
from marshmallow.decorators import post_dump
from marshmallow.exceptions import ValidationError
from slugify import slugify
from sqlalchemy import desc, func

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SECRET_KEY"] = config("SECRET_KEY", default="i-am-not-a-secret-hahaha")

###################################################################
db_uri = config("DATABASE_URL", default="sqlite:///voters.db")
if db_uri.startswith("postgres://"):
    db_uri = db_uri.replace("postgres://", "postgresql://", 1)
##################################################################

app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = config(
    "SQLALCHEMY_TRACK_MODIFICATIONS", default=False
)

db = SQLAlchemy(app)
cors = CORS(app)
migrate = Migrate(app, db)

algod_address = "https://node.testnet.algoexplorerapi.io"
algod_token = "fi0QdbiBVl8hsVMCA2SUg6jnQdvAzxY48Zy2G6Yc"

indexer_address = "https://algoindexer.testnet.algoexplorerapi.io"
headers = {"x-api-key": algod_token}

algod_client = algod.AlgodClient(algod_token, algod_address, headers)
indexer_client = indexer.IndexerClient(algod_token, indexer_address, headers)


###################################################################
# MODELS
###################################################################
class Wallet(db.Model):
    """This model represents a wallet."""

    __tablename__ = "wallets"

    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(constants.ADDRESS_LEN), nullable=False)

    def __repr__(self) -> str:
        return "<Wallet {}>".format(self.address)

    @staticmethod
    def get_or_create(address):
        """Creates or gets a `Wallet` instance."""
        instance = Wallet.query.filter_by(address=address).first()
        if not instance:
            new_wallet = Wallet(address=address)
            db.session.add(new_wallet)
            db.session.commit()

            return new_wallet
        return instance


class Election(db.Model):
    """An election model represents the voting process."""

    __tablename__ = "elections"

    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey("wallets.id"), nullable=False)
    wallet = db.relationship("Wallet", backref=db.backref("elections", lazy="dynamic"))

    title = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(150), index=True, nullable=False, unique=True)

    description = db.Column(db.Text, nullable=True)

    algo_per_vote = db.Column(db.Integer, nullable=False)

    process_image = db.Column(db.LargeBinary, nullable=True)

    created_at = db.Column(db.DateTime, default=func.now())
    end_at = db.Column(db.DateTime, nullable=True)

    voters = db.relationship('Voter', backref='election', lazy='dynamic')

    is_started = db.Column(db.Boolean, default=False)
    is_finished = db.Column(db.Boolean, default=False)

    def __init__(self, wallet_id, title, description, process_image, algo_per_vote=10) -> None:
        self.title = title
        self.description = description
        self.slug = slugify(title) + "-" + secrets.token_hex(3)
        self.wallet_id = wallet_id
        self.process_image = process_image
        self.algo_per_vote = algo_per_vote

    def __repr__(self) -> str:
        return "<Election wallet={} title={} algo_per_vote={} voters={}>".format(
            self.wallet,
            self.title,
            self.algo_per_vote,
            len(self.voters.all())
        )


class Candidate(db.Model):
    """A candidate model represents the choices available for an election."""

    __tablename__ = "candidates"
    id = db.Column(db.Integer, primary_key=True)

    election_id = db.Column(db.Integer, db.ForeignKey("elections.id"), nullable=False)
    election = db.relationship("Election", backref=db.backref("candidates", lazy="dynamic"))

    name = db.Column(db.String(100), nullable=False)
    image = db.Column(db.LargeBinary, nullable=True)

    address = db.Column(db.String(constants.ADDRESS_LEN), nullable=False, unique=True)
    private_key = db.Column(db.Text, nullable=False, unique=True)

    def __init__(self, election_id, name, address, private_key, image=None) -> None:
        self.election_id = election_id
        self.name = name
        self.image = image
        self.address = address
        self.private_key = private_key


class Voter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    election_id = db.Column(db.Integer, db.ForeignKey("elections.id"), nullable=False)
    address = db.Column(db.String(constants.ADDRESS_LEN), nullable=False)
    matric_no = db.Column(db.String(40), nullable=False)

    def __init__(self, election_id, address, matric_no) -> None:
        self.election_id = election_id
        self.address = address
        self.matric_no = matric_no

    def __repr__(self) -> str:
        return "<Voter election={} address={} matric_no={}>".format(
            self.election_id,
            self.address,
            self.matric_no,
        )


##################################################################################################
# SERIALIZERS
##################################################################################################
class WalletSchema(Schema):
    address = fields.Str(required=True)


class CandidateSchema(Schema):
    name = fields.Str(required=True)
    image = fields.Str()

    address = fields.Str(required=True)
    private_key = fields.Str(required=True, load_only=True)

    @post_dump(pass_original=True)
    def add_votes(self, data, original_data, **kwargs):
        if original_data.election.is_started:
            votes = count(indexer_client, original_data.address) / (
                original_data.election.algo_per_vote * 1_000_000
            )
            data["votes"] = votes
            return data

        data["votes"] = 0
        return data

    @post_dump(pass_original=True)
    def decode_img(self, data, original_data, **kwargs):
        image = original_data.image
        if image:
            data["image"] = image.decode("utf-8")

        return data


class VotersSchema(Schema):
    address = fields.String(required=True)
    matric_no = fields.String(required=True)


class ElectionSchema(Schema):
    title = fields.Str(required=True)
    slug = fields.Str(dump_only=True)

    description = fields.Str(required=False)

    process_image = fields.Str(required=False)

    candidates = fields.List(fields.Nested(CandidateSchema))
    voters = fields.List(fields.Nested(VotersSchema))

    algo_per_vote = fields.Int(required=True)

    is_started = fields.Bool(dump_only=True)
    is_finished = fields.Bool(dump_only=True)

    created_at = fields.DateTime(dump_only=True)
    end_at = fields.DateTime(dump_only=True)

    @post_dump(pass_original=True)
    def add_wallet(self, data, original_data, **kwargs):
        wallet = WalletSchema().dump(original_data.wallet)
        data["wallet"] = wallet
        return data

    @post_dump(pass_original=True)
    def decode_img(self, data, original_data, **kwargs):
        image = original_data.process_image
        if image:
            data["process_image"] = image.decode("utf-8")

        return data


class StartElectionSchema(Schema):
    end_at = fields.DateTime(required=True)


################################################################################################
# DECORATORS & UTILITY FUNCTIONS
################################################################################################
def wallet_required(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        address = request.headers.get("X-Wallet-Address", None)
        if not address:
            return (
                jsonify(status="error", message="An address is needed to authorize this request"),
                401,
            )
        if not encoding.is_valid_address(address):
            return (
                jsonify(status="error", message="Invalid address passed!"),
                400,
            )
        return f(*args, **kwargs)

    return wrapper


def is_election_owner(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        address = request.headers.get("X-Wallet-Address", None)

        election = Election.query.filter_by(slug=kwargs.get("slug")).first()
        if not election:
            return jsonify(status="error", message="Election does not exist!"), 404

        if election.wallet.address != address:
            return jsonify(status="error", message="You are not authorized for this action"), 403

        return f(*args, **kwargs)

    return wrapper


def election_exists(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        election = Election.query.filter_by(slug=kwargs.get("slug")).first()
        if not election:
            return jsonify(status="error", message="Election does not exist!"), 404

        return f(*args, **kwargs)

    return wrapper


def get_wallet_from_headers() -> str:
    """Returns the wallet from `request.headers`"""
    address = request.headers.get("X-Wallet-Address")

    return address


def database_is_empty():
    table_names = sqlalchemy.inspect(db.engine).get_table_names()
    is_empty = table_names == []
    return is_empty


def count(indexer_client: 'indexer.IndexerClient', address):
    return indexer_client.account_info(address)['account']['amount']


def count_votes(candidates, choice_per_vote):
    labels = []
    values = []
    for candidate in candidates:
        _ = count(candidate.address)
        labels.append(candidate.name)
        values.append(_ / 1_000_000)
    print(labels, values)
    return labels, values


def get_choice_committed_to_address(indexer_client: indexer.IndexerClient, address):
    transactions = indexer_client.search_transactions_by_address(
        address,
        txn_type="pay",
    )
    txns = [
        {
            "receiver": txn["payment-transaction"]["receiver"],
            "amount": txn["payment-transaction"]["amount"],
        }
        for txn in transactions["transactions"]
    ]

    return txns


##################################################################################################
# VIEWS
#################################################################################################
@app.get("/")
def index():
    return (jsonify(status="success", message="Welcome to Choice API", data=None), 200)


@app.post("/elections/create")
@wallet_required
def create_election():
    """First endpoint in creating an election."""
    wallet_address = get_wallet_from_headers()

    request_data = request.get_json()
    if not request_data:
        return (
            jsonify(
                status="error",
                message="Set the mimetype header to application/json",
                data=None,
            ),
            400,
        )
    schema = ElectionSchema()
    try:
        wallet = Wallet.get_or_create(wallet_address)
        data = schema.load(request_data)

        new_election = Election(
            wallet_id=wallet.id,
            title=data["title"],
            description=data.get("description"),
            process_image=data.get("process_image", "").encode("utf-8"),
            algo_per_vote=data["algo_per_vote"],
        )
        db.session.add(new_election)
        db.session.flush()

        all_candidates = data["candidates"]

        for candidate in all_candidates:
            new_candidate = Candidate(
                election_id=new_election.id,
                name=candidate["name"],
                address=candidate["address"],
                image=candidate.get("image", "").encode("utf-8"),
                private_key=candidate["private_key"],
            )
            db.session.add(new_candidate)

        db.session.commit()

        response = schema.dump(new_election)
        return (
            jsonify(status="success", message="Election created successfully!", data=response),
            201,
        )
    except ValidationError as err:
        print(err)
        return jsonify(status="error", message="Validation Failed", data=err.messages), 400


@app.get("/elections/mine")
@wallet_required
def my_elections():
    schema = ElectionSchema(many=True)

    wallet_address = get_wallet_from_headers()
    wallet = Wallet.get_or_create(wallet_address)

    elections = (
        Election.query.filter_by(wallet_id=wallet.id).order_by(desc(Election.created_at)).all()
    )
    response = schema.dump(elections)

    return (
        jsonify(
            status="success",
            message="Personal elections returned successfully!",
            data=response,
        ),
        200,
    )


@app.get("/elections")
def all_elections():
    schema = ElectionSchema(many=True)

    elections = (
        Election.query.filter_by(is_started=True, is_finished=False)
        .order_by(desc(Election.created_at))
        .all()
    )
    response = schema.dump(elections)

    return (
        jsonify(
            status="success",
            message="All elections returned successfully!",
            data=response,
        ),
        200,
    )


@app.post("/elections/<slug>/start")
@wallet_required
@is_election_owner
def start_election(slug):
    request_data = request.get_json()
    if not request_data:
        return (
            jsonify(
                status="error",
                message="Set the mimetype header to application/json",
                data=None,
            ),
            400,
        )
    parsed_data = StartElectionSchema().load(request_data)
    election = Election.query.filter_by(slug=slug).first()

    election.is_started = True
    election.end_at = parsed_data['end_at']
    election.is_finished = False

    db.session.commit()

    return jsonify(status="success", message="Election started successfully!"), 200


@app.post("/elections/<slug>/voters")
def add_voters(slug):
    request_data = request.get_json()
    if not request_data:
        return (
            jsonify(
                status="error",
                message="Set the mimetype header to application/json",
                data=None,
            ),
            400,
        )
    parsed_data = VotersSchema().load(request_data)
    election = Election.query.filter_by(slug=slug).first()
    if not election:
        return (
            jsonify(
                status="error",
                message="Election does not exist!",
                data=None,
            ),
            404,
        )

    if election.is_started and not election.is_finished:
        voter = Voter(
            election_id=election.id,
            address=parsed_data['address'],
            matric_no=parsed_data['matric_no']
        )
        db.session.add(voter)
        db.session.commit()

        return jsonify(status="success", message="Voter added successfully!"), 200

    return jsonify(status="success", message="You cannot a voter to an election that has not started or has already finished."), 400


@app.post("/elections/<slug>/end")
@wallet_required
@is_election_owner
def end_election(slug):
    election = Election.query.filter_by(slug=slug).first()

    election.is_started = False
    election.is_finished = True

    db.session.commit()

    return jsonify(status="success", message="Election started successfully!"), 200


@app.post("/elections/<slug>/delete")
@wallet_required
@is_election_owner
def delete_election(slug):
    election = Election.query.filter_by(slug=slug).first()

    db.session.delete(election)
    db.session.commit()

    return jsonify(status="success", message="Election deleted successfully!"), 204


@app.get("/elections/<slug>/results")
@election_exists
def view_result(slug):
    election = Election.query.filter_by(slug=slug).first()

    labels, values = count_votes(election.candidates.all(), election.choice_per_vote)

    return (
        jsonify(
            status="success",
            message="Result fetched successfully!",
            data={"labels": labels, "values": values},
        ),
        200,
    )


@app.get("/committed/<address>")
def amount_committed_to_address(address):
    if not encoding.is_valid_address(address):
        return jsonify(status="error", message="Invalid address provided!"), 400

    candidates = Candidate.query.all()
    candidates = [candidate.address for candidate in candidates]

    transactions = get_choice_committed_to_address(indexer_client, address)
    amount = 0

    for transaction in transactions:
        if transaction["receiver"] in candidates:
            amount += transaction["amount"] / 100

    return (
        jsonify(
            status="success",
            data={"amount": amount},
            message="Amount committed to governance returned successfully!",
        ),
        200,
    )

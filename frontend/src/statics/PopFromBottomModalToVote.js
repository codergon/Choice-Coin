import ScrollText from "../components/ScrollText";
import MyAlgoConnect from "@randlabs/myalgo-connect";
import algosdk from "algosdk";
import { useSelector, useDispatch } from "react-redux";

const PopFromBottomModalToVote = () => {
  const dispatch = useDispatch();

  const algodClient = new algosdk.Algodv2(
    "",
    "https://node.testnet.algoexplorerapi.io",
    ""
  );
  const indexerClient = new algosdk.Indexer(
    "",
    "https://algoindexer.testnet.algoexplorerapi.io",
    ""
  );

  const { openModalVote, voteData } = useSelector(
    (state) => state.status.voteModal
  );

  const myAlgoConnect = async () => {
    const myAlgoWallet = new MyAlgoConnect();

    try {
      const accounts = await myAlgoWallet.connect({
        shouldSelectOneAccount: true,
      });
      const address = accounts[0].address;

      const myAccountInfo = await indexerClient.lookupAccountByID(address).do();

      // get balance of the voter
      const balance = myAccountInfo.account.amount / 1000000;

      if (voteData.amount > balance) {
        alert("You do not have sufficient balance to make this transaction.");
        return;
      }

      const suggestedParams = await algodClient.getTransactionParams().do();
      const amountToSend = voteData.amount * 1000000;

      const txn = algosdk.makePaymentTxnWithSuggestedParamsFromObject({
        from: address,
        to: voteData.address,
        amount: amountToSend,
        suggestedParams,
      });

      const signedTxn = await myAlgoWallet.signTransaction(txn.toByte());
      await algodClient.sendRawTransaction(signedTxn.blob).do();

      // close modal.
      dispatch({ type: "close_vote_modal" });

      // alert success
      alert("You have successfully placed your vote for this election");
    } catch (error) {
      console.log(error);
    }
  };

  const algoSignerConnect = async () => {
    try {
      if (typeof window.AlgoSigner === "undefined") {
        window.open(
          "https://chrome.google.com/webstore/detail/algosigner/kmmolakhbgdlpkjkcjkebenjheonagdm",
          "_blank"
        );
      } else {
        const accounts = await window.AlgoSigner.accounts({
          ledger: "TestNet",
        });
        const address = accounts[0].address;

        const myAccountInfo = await indexerClient
          .lookupAccountByID(address)
          .do();

        // get balance of the voter
        const balance = myAccountInfo.account.amount / 1000000;

        if (voteData.amount > balance) {
          alert("You do not have sufficient balance to make this transaction.");
          return;
        }

        const suggestedParams = await algodClient.getTransactionParams().do();
        const amountToSend = voteData.amount * 1000000;

        const txn = algosdk.makePaymentTxnWithSuggestedParamsFromObject({
          from: address,
          to: voteData.address,
          amount: amountToSend,
          suggestedParams,
        });

        const signedTxn = await window.AlgoSigner.signTxn([
          { txn: window.AlgoSigner.encoding.msgpackToBase64(txn.toByte()) },
        ]);
        await algodClient
          .sendRawTransaction(
            window.AlgoSigner.encoding.base64ToMsgpack(signedTxn[0].blob)
          )
          .do();

        // close modal.
        dispatch({ type: "close_vote_modal" });

        // alert success
        alert("You have successfully placed your vote for this election");
      }
    } catch (error) {
      alert("An error occured while trying to connect AlgoSigner");
    }
  };

  return (
    <menu
      className="mn_sm"
      style={{ display: `${!!openModalVote ? "flex" : "none"}` }}
    >
      <div
        style={{ width: "100%", flex: 1 }}
        onClick={() => {
          dispatch({ type: "close_vote_modal" });
        }}
      ></div>

      <div className="mn_sm_modal">
        <div className="mn_sm_modal_inn">
          <>
            <div className="algo_connect_hd">Select Wallet to continue</div>

            <div className="connect_butt" onClick={myAlgoConnect}>
              <div className="connect_wallet_img">
                <img
                  src="https://i.postimg.cc/76r9kXSr/My-Algo-Logo-4c21daa4.png"
                  alt=""
                />
              </div>
              <p className="connect_wallet_txt">My Algo Wallet</p>
            </div>
            <div className="connect_butt" onClick={algoSignerConnect}>
              <div className="connect_wallet_img">
                <img
                  src="https://i.postimg.cc/L4JB4JwT/Algo-Signer-2ec35000.png"
                  alt=""
                />
              </div>
              <p className="connect_wallet_txt">
                {typeof AlgoSigner === undefined
                  ? "Install AlgoSigner"
                  : "AlgoSigner"}
              </p>
            </div>
          </>

          <ScrollText word={"Decentralized decisions"} />
        </div>
      </div>
    </menu>
  );
};

export default PopFromBottomModalToVote;

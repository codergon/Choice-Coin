import axios from "axios";
import "../styles/landing.css";
import { URL } from "../constants";
import { useQuery } from "react-query";
import loadable from "@loadable/component";
const ScrollTextLand = loadable(() => import("../components/ScrollTextLand"));

const Landing = () => {
  //

  const walletAddress = localStorage.getItem("address");

  const { isLoading, error, data } = useQuery("committed", () =>
    axios
      .get(`${URL}/committed/${walletAddress}`)
      .then((response) => response.data.data)
  );

  return (
    <div className="landing" id="landing">
      <ScrollTextLand
        word={"Decentralised NACOS Voting System Using Algorand"}
      />
      <div
        style={{
          width: "100%",
          height: "20px",
          fontSize: "13px",
          fontWeight: "500",
          marginTop: "10px",
          textTransform: "uppercase",
        }}
      >
        Amount committed to Governance: {!isLoading && !error && data.amount}{" "}
        $ALGO
      </div>

      <div className="land_cov">
        <div className="land_item1">
          <p className="hdy">NACOS</p>
          <p className="suby">
            NACOS Voting System using Algorand Blockchain
            <br />
            <br />
            Decentralized Decisions enables organizations to make governance
            decisions in an open and decentralized manner.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Landing;

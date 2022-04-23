import { useEffect, useState } from "react";
import algosdk from "algosdk";
import MyAlgoConnect from "@randlabs/myalgo-connect";
import { useWindowSize } from "@react-hook/window-size";
import { CopyToClipboard } from "react-copy-to-clipboard";

const TopNavigationBar = ({ darkTheme }) => {
  const [width] = useWindowSize();
  const [balance, setBalance] = useState(0);

  const indexerClient = new algosdk.Indexer(
    {
      "X-API-Key": "bbb ",
    },
    "https://algoindexer.testnet.algoexplorerapi.io",
    ""
  );

  const walletAddress = localStorage.getItem("address");

  useEffect(() => {
    const setMyBalance = async () => {
      const myAccountInfo = await indexerClient
        .lookupAccountByID(walletAddress)
        .do();

      const b = myAccountInfo.account.amount / 1000000;
      setBalance(b);
    };

    setMyBalance();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const myAlgoConnect = async () => {
    const myAlgoWallet = new MyAlgoConnect();

    try {
      const accounts = await myAlgoWallet.connect({
        shouldSelectOneAccount: true,
      });
      const address = accounts[0].address;

      // close modal.
      localStorage.setItem("wallet-type", "my-algo");
      localStorage.setItem("address", address);

      window.location.reload();
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
        console.log(window.AlgoSigner.accounts);
        await window.AlgoSigner.connect({
          ledger: "TestNet",
        });
        const accounts = await window.AlgoSigner.accounts({
          ledger: "TestNet",
        });

        const address = accounts[0].address;

        // close modal.
        localStorage.setItem("wallet-type", "algosigner");
        localStorage.setItem("address", address);

        window.location.reload();
      }
    } catch (error) {
      alert("AlgoSigner not set up yet!");
    }
  };

  const isWalletConnected =
    localStorage.getItem("wallet-type") === null ? false : true;

  return (
    <header className="small_header">
      <div
        className="notResponsiveWarning"
        style={{ display: width > 800 ? "flex" : "none" }}
      >
        <p>
          {
            "/////// This site is not responsive yet. Large screen view coming soon."
          }
        </p>
      </div>

      <div className="small_header_inn">
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            textTransform: "uppercase",
          }}
        >
          NACOS VOTING PLATFORM
        </div>

        {!!isWalletConnected ? (
          <div className="addrDisplay">
            <div className="addrDisplayInn">
              <div className="addrBalance">{balance} $ALGO</div>

              <CopyToClipboard text={walletAddress}>
                <div className="addressTxt">
                  <p>{walletAddress}</p>
                  <i className="uil uil-copy"></i>
                </div>
              </CopyToClipboard>
            </div>
          </div>
        ) : (
          <div className="dropDownConnect">
            <div className="dropDownConnect_button">
              <button className="connect_wallet_button">
                <p>
                  Connect Wallet
                  <i
                    className="uil uil-angle-down"
                    style={{ fontSize: "18px" }}
                  />
                </p>
              </button>
            </div>

            <div className="dropDownConnect_items">
              <div className="dropDownConnect_item" onClick={myAlgoConnect}>
                <div className="dropDownConnect_img">
                  <img
                    src="https://i.postimg.cc/76r9kXSr/My-Algo-Logo-4c21daa4.png"
                    alt=""
                  />
                </div>
                <p className="dropDownConnect_item_txt">My Algo Wallet</p>
              </div>
              <div className="dropDownConnect_item" onClick={algoSignerConnect}>
                <div className="dropDownConnect_img">
                  <img
                    src="https://i.postimg.cc/L4JB4JwT/Algo-Signer-2ec35000.png"
                    alt=""
                  />
                </div>
                <p className="dropDownConnect_item_txt">
                  {typeof window.AlgoSigner === undefined
                    ? "Install AlgoSigner"
                    : "AlgoSigner"}
                </p>
              </div>
            </div>
          </div>
        )}
        {/*  */}
      </div>
    </header>
  );
};

export default TopNavigationBar;

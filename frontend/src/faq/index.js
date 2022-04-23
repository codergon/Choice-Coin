import $ from "jquery";
import "../styles/faq.css";

const Faq = () => {
  return (
    <div className="faq_cont">
      <div className="faq_cont_inn">
        <div className="faq_hd">
          <p>
            <i className="uil uil-question-circle"></i> Frequently Asked
            Questions
          </p>
        </div>

        {[
          {
            que: " About Algorand",
            ans: "Algorand is a blockchain-based cryptocurrency platform that aims to be secure, scalable, and decentralized. The Algorand platform supports smart contract functionality, and its consensus algorithm is based on proof-of-stake principles and a Byzantine Agreement protocol. Algorand's native cryptocurrency is called Algo.",
          },
        ].map((item) => (
          <div className="collap_cov">
            <button
              className="collapsible"
              onClick={(e) => {
                $(e.target).toggleClass("colap_active");

                var content = $(e.target)
                  .closest(".collap_cov")
                  .find(".collap_cont");

                if (!!content.height()) {
                  content.css({
                    maxHeight: "0px",
                  });
                } else {
                  content.css({
                    maxHeight: content.get(0).scrollHeight + "px",
                  });
                }
              }}
            >
              <p>{item.que}</p>
            </button>
            <div className="collap_cont">
              <p>{item.ans}</p>
            </div>
          </div>
        ))}

        <div className="ask_q_sect">
          <button className="ask_que">
            <p>
              Ask a question or contribute{" "}
              <i className="uil uil-arrow-up-right"></i>
            </p>
          </button>
        </div>
      </div>
    </div>
  );
};

export default Faq;

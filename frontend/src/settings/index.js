import "../styles/settings.css";
import Toggle from "../components/Toggle";
import { useSelector } from "react-redux";

const Participate = () => {
  const darkTheme = useSelector((state) => state.status.darkTheme);

  const LogOut = () => {
    localStorage.clear();
    window.location.reload();
    console.log("data");
  };

  return (
    <>
      <div className="settings">
        <div className="settings_inn">
          <div className="settings_hd">
            <p>Settings</p>
          </div>
          {/*  */}

          <div className="toggleDarkTheme">
            <div className="togglyButt">
              <p>{darkTheme ? "Light Theme" : "Dark Theme"}</p>
              <div className="theme_tog">
                <Toggle darkTheme={darkTheme} />
              </div>
            </div>

            <div className="logOutButt" onClick={LogOut}>
              <p>
                Log Out{" "}
                <i className="uil uil-signout" style={{ fontSize: "16px" }}></i>
              </p>
            </div>
          </div>

          {/*  */}
        </div>
      </div>
    </>
  );
};

export default Participate;

import Voting from "./Voting/Voting";
import Navbar from "./Navbar/Navbar"

const { useState, useEffect } = React;

const App = () => {

  /*#################################################################*/
  /*####################### UTILITY FUNCTIONS #######################*/
  /*#################################################################*/ 
  
  function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      var cookies = document.cookie.split(';');
      for (var i = 0; i < cookies.length; i++) {
        var cookie = jQuery.trim(cookies[i]);
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  const post = (url, data) => {
    var fdata = {
      body: JSON.stringify(data),
      headers: {
        'content-type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      method: 'POST',
    };

    if (votingUserData) {
      fdata.headers['Authorization'] = 'Token ' + votingUserData.token;
    }

    return fetch(url, fdata)
      .then(response => {
        if (response.status === 200) {
          return response.json();
        } else {
          return Promise.reject(response.statusText);
        }
      });
  }

  const getVotingUserData = () => {

    utils.post("/authentication/decide/getVotingUser/")
      .then(res => {
        setVotingUserData(res);
      })
      .catch(error => {
        console.log(error)//this.showAlert("danger", '{% trans "Error: " %}' + error);
      });
  }

  /*#####################################################*/
  /*####################### STATE #######################*/
  /*#####################################################*/

  const [votingUserData, setVotingUserData] = useState(null);
  const [alert, setAlert] = useState({ lvl: null, msg: null, });

  
  /*#############################################################*/
  /*####################### FUNCTIONALITY #######################*/
  /*#############################################################*/

  //Run only once
  useEffect(() => {
    getVotingUserData();
  }, [])

  const utils = { alert, setAlert, post, votingUserData }
  

  /*####################################################*/
  /*####################### VIEW #######################*/
  /*####################################################*/

  return (
    
    <div className="App">

      <Navbar utils={utils} />


      {/* <h1>Please vote {voting.id} - {voting.name}</h1> */}

      {votingUserData && <Voting utils={utils} />}

    </div>
  );
}

const domContainer = document.querySelector('#react-root');
ReactDOM.render(<App />, domContainer);
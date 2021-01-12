'use strict';
const { useState, useEffect } = React

const Login = ({ utils }) => {

    /*############### STATE ###############*/

    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');


    /*############### UTILITY FUNCTIONS ###############*/
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

    const getUser = (tkn) => {
        var data = { token: tkn };
        utils.post("/gateway/authentication/getuser/", data)
            .then(data => {
                utils.setUser(data);
            }).catch(error => {
                console.log(error)//this.showAlert("danger", '{% trans "Error: " %}' + error);
            });
    }

    const getVotingUser = () => {
        var data = { };
        utils.post("/authentication/decide/getVotingUser/", data)
            .catch(error => {
                console.log(error)//this.showAlert("danger", '{% trans "Error: " %}' + error);
            });
    }

    const init = () => {
        const cookies = document.cookie.split("; ");

        cookies.forEach((c) => {
            var cs = c.split("=");
            if (cs[0] == 'decide' && cs[1]) {
                utils.setToken(cs[1]);
                getUser(cs[1]);
            }
        });

        ElGamal.BITS = keybits;
    }

    const onSubmitLogin = (event) => {
        event.preventDefault();

        const form = { username, password, csrftoken};

        utils.post("/gateway/authentication/login/", form)
            .then(data => {
                document.cookie = 'decide=' + data.token + ';';
                utils.setToken(data.token);
                getUser(data.token);
                getVotingUser();
            })
            .catch(error => {
                utils.setAlert({ lvl: 'danger', msg: 'Error: ' + error, });
            });
    }


    /*############### FUNCTIONALITY ###############*/

    useEffect(() => {
        init();
    }, [])


    /*############### RETURN ###############*/
    var csrftoken = getCookie('csrftoken');

    return (
        <div className="login">
            <form onSubmit={onSubmitLogin}>
                <label>Username</label>
                <input
                    type="text"
                    value={username}
                    onChange={e => setUsername(e.target.value)}
                    autoComplete="username"
                    required
                />

                <label>Password</label>
                <input
                    type="password"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    autoComplete="current-password"
                    required
                />

                <input type="hidden" name="csrfmiddlewaretoken" value={csrftoken} />

                <button>Login</button>

            </form>
        </div>
    );
}
export default Login;
"use strict";
const { useState, useEffect } = React;

const Navbar = ({ utils }) => {
  const logout = () => {
    const data = { token: utils.token };
    utils.post("/gateway/authentication/logout/", data);
    utils.setToken(null);
    utils.setUser(null);
    document.cookie = "decide=;";
  };

  



  return (
    <div >
      <nav className="navbar navbar-expand-lg navbar-dark" id="voting-nav">

        {/* <a class="navbar-brand js-scroll-trigger" href="#page-top"><img src="assets/img/navbar-logo.svg" alt="" /></a> */}
        <div>
          {" "}
          <h1 className="white">Voting navbar</h1>{" "}
        </div>

        {/* <button class="navbar-toggler navbar-toggler-right" type="button" data-toggle="collapse" data-target="#navbarResponsive" aria-controls="navbarResponsive" aria-expanded="false" aria-label="Toggle navigation">
                        Menu
                        <i class="fas fa-bars ml-1"></i>
                    </button> */}

        {/* <div class="collapse navbar-collapse" id="navbarResponsive">
          <ul class="navbar-nav text-uppercase ml-auto">
            <li class="nav-item">
              <a class="nav-link js-scroll-trigger" href="#candidatura1">
                Candidatura 1
              </a>
            </li>
            <li class="nav-item">
              <a class="nav-link js-scroll-trigger" href="#candidatura2">
                Candidatura 2
              </a>
            </li>
            <li class="nav-item">
              <a class="nav-link js-scroll-trigger" href="#candidatura3">
                Candidatura 3
              </a>
            </li>
            <li class="nav-item">
              <a class="nav-link js-scroll-trigger" href="#candidatura4">
                Candidatura 4
              </a>
            </li>
            <li class="nav-item">
              <a class="nav-link js-scroll-trigger" href="#candidatura5">
                Candidatura 5
              </a>
            </li>
            <li class="nav-item">
              <a class="nav-link js-scroll-trigger" href="#candidatura6">
                Candidatura 6
              </a>
            </li>
            <li class="nav-item">
              <a class="nav-link js-scroll-trigger" href="#candidaturaExtra">
                10 Candidatos
              </a>
            </li>
          </ul>
        </div> */}

        <div>
          {utils.user ? <button onClick={logout}>Logout</button> : null}
    
        </div>
        </nav>
    </div>
  );
};

export default Navbar;
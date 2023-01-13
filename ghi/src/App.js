import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import "./App.css";
import Nav from "./Nav";
// import SignUpForm from "./accounts/SignUpForm";
// import LoginForm from "./accounts/LoginForm";
import EventList from "./EventList";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Nav />
        <Routes>
          {/* <Route path="/login" element={<LoginForm />}></Route>
          <Route path="/signup" element={<SignUpForm />}></Route> */}
          <Route path="/events" element={<EventList />}></Route>
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;

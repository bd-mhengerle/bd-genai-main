import React from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import { StateProvider } from './StateContext';
import { QueryClient, QueryClientProvider } from "react-query"
import { MainComponent} from './components/Main'

const queryClient = new QueryClient()

function App() {
  return (
    <StateProvider>
      <QueryClientProvider client={queryClient}>
        <Router>
          <div className="body" data-testid="header-component">
            <Routes>
              <Route path="/" element={<MainComponent />} />
              <Route path="/:id" element={<MainComponent />} />
            </Routes>
            <ToastContainer />
          </div>
        </Router>
      </QueryClientProvider>
    </StateProvider>
  );
}

export default App;
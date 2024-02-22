import React, { useState, useEffect} from 'react'
import './App.css';
import MonitoringComponent from './MonitoringComponent'


function App() {

  const [pdfFile, setPdfFile] = useState(null);
  const [userQuestion, setUserQuestion] = useState('');
  const [result, setResult] = useState([]);
  const [activeTab, setActiveTab] = useState('form');
  // const [aiMessages, setAiMessages] = useState([]);
  // const [userMessages, setUserMessages] = useState([]);
  const [chatHistory, setChatHistory] = useState([]);


  useEffect(() => {
    const handleResultChange = () => {
      const newUserMessages = [];

      result.forEach(message => {
        if (message.question) {
          newUserMessages.push({ text: message.question });
        } 
        if (message.answer) {
          newUserMessages.push({text: message.answer });
        }
      });
      
      setChatHistory(newUserMessages);
      // setAiMessages(newAiMessages);

    };
  
    handleResultChange();
  }, [result]); 

  const handleQuestionChange = (event) => {
    setUserQuestion(event.target.value);
  }

  const handleFileChange = (event) => {
    setPdfFile(event.target.files[0]);
  };

  const handleSubmit = (event) => {
    event.preventDefault();

    const formData = new FormData();

    if (pdfFile) {
      formData.append("file", pdfFile);
    }
    if (userQuestion) {
      formData.append('question', userQuestion);
    }

    fetch("http://127.0.0.1:5000/process_pdf", {
      method: "POST",
      body: formData,

    })
      .then((response) => {
        console.log("PDF file sent successfully");
        console.log(response)
        return response.json();
      })
      .then((data) => {
        console.log("hi1")
        setResult(data?.chat || 'No answer found'); //name the same as python result
        console.log(data?.chat)
        if (data.statusCode === 200 && data.chat.length === 0) {
          window.location.reload();
        }
      })
      .catch((error) => {
        console.log("hi")
        console.error("Error", error);
      });
  };

  const switchToFormTab = () => {
    setActiveTab('form');
  };

  const switchToMonitoringTab = () => {
    setActiveTab('monitoring');
  };


  return (
    <div className='tot-container'>
      <h1 className='header'>LangGuard</h1>
      <div className="tab-container">
        <button onClick={switchToFormTab} id='form-button' className={activeTab === 'form' ? 'active-tab' : ''}>
          Q-A
        </button>
      </div>
      {activeTab === 'form' && (
        <div>
          <h4>Enter Exit | Leave | End to end/restart the program ⏹️</h4>
          <h4>You can only upload the pdf ONCE and keep asking questions on it 😊!</h4>
          <div className="form-container">
            <form onSubmit={handleSubmit} className="submit-button">
              <label className="q-box-container" htmlFor="question">
                Question:
              </label>
              <input
                className="q-box"
                id="question"
                type="text"
                value={userQuestion}
                onChange={handleQuestionChange}
                placeholder="Ask your question here"
              />
              <div>
                  <label htmlFor="file">Select PDF File:</label>
                  <input type="file" id="file" accept=".pdf" onChange={handleFileChange} />
              </div>
              <button className="submit-box" type="submit" disabled={!pdfFile || !userQuestion}>
                Submit
              </button>
            </form>
          </div>
          <div className="chat-history-container">
            <h2>Chat history</h2>
            <ul>
              {chatHistory.map((message, index) => (
                <li key={index}>{message.text}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>

  );
}

export default App;

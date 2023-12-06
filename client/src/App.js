import React, { useState } from 'react'
import './App.css';


// function App() {
//   const [question, setQuestion] = useState('');
//   const [answerFormat, setAnswerFormat] = useState('');
//   const [result, setResult] = useState('');

//   const handleSubmit = async (e) => {
//     e.preventDefault();

//     try {
//       const response = await fetch('http://127.0.0.1:5000/query_open_ai', {
//         method: 'POST',
//         headers: {
//           'Content-Type': 'application/json',
//         },
//         body: JSON.stringify({
//           prompt: `${question}\n${answerFormat}`,
//         }),
//       });

//       if (!response.ok) {
//         throw new Error(`HTTP error! Status: ${response.status}`);
//       }

//       const data = await response.json();
//       setResult(data.body);
//     } catch (error) {
//       console.error('Error:', error);
//       setResult('Error occurred');
//     }
//   };

//   return (
//     <div className='big-container'>
//       <form className='submit-button' onSubmit={handleSubmit}>
//         <label className="q-box-container">
//           Question:
//           <input
//             className="q-box"
//             type="text"
//             value={question}
//             onChange={(e) => setQuestion(e.target.value)}
//           />
//         </label>
//         <br />
//         <label className="q-box-container">
//           Answer Format:
//           <input
//             className="q-box"
//             type="text"
//             value={answerFormat}
//             onChange={(e) => setAnswerFormat(e.target.value)}
//           />
//         </label>
//         <br />
//         <button className="submit-box" type="submit">Submit</button>
//       </form>
//       <div>
//         <h3>Result:</h3>
//         <p>{result}</p>
//       </div>
//     </div>
//   );
// }

// export default App;


function App() {
  const [pdfFile, setPdfFile] = useState(null);
  const [userQuestion, setUserQuestion] = useState('');
  const [result, setResult] = useState('');
  const [id, setID] = useState('');

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
  if(userQuestion) {
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
      setResult(data?.ans|| 'No answer found'); //name the same as python result
      console.log(data?.ans)
      setID(data.id);
    })
    .catch((error) => {
      console.error("Error", error);
    });
  };

  //fetch("http://127.0.0.1:5000/process_pdf/" + id, {

  return (
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
        <label className="csv-block" htmlFor="file">
          Upload PDF file:
        </label>
        <input
          type="file"
          id="file"
          name="file"
          accept=".pdf"
          onChange={handleFileChange}
          className="mb-3"
        />
        <button
          className="submit-box"
          type="submit"
          disabled={!pdfFile || !userQuestion}
        >
          Submit
        </button>
      </form>
      <p className="result-box">Result: {result}</p>
    </div>
  );
}

export default App;

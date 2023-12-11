import React, {useState, useEffect} from 'react';
import './App.css';

function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
  
    const formattedTime = `${minutes}:${remainingSeconds < 10 ? '0' : ''}${remainingSeconds}`;
  
    return formattedTime;
  }

const MonitoringComponent = ({ tokenCountsHistory }) => {
    const [selectedModel, setSelectedModel] = useState('gpt-3.5-turbo');
    const [limits, setLimits] = useState({
        'gpt-3.5-turbo': 40000,
        //add others
        'text-embedding-ada-002': 150000,
        'text-embedding-ada-002-T1': 1000000,
        'gpt-4': 10000
    })
    const [tokenCount, setTokenCount] = useState('');
    const [currentTime, setCurrentTime] = useState('');

    const handleModelChange = (e) => {
        setSelectedModel(e.target.value);
    };

    useEffect(() => {
        const fetchData = async () => {
          try {
            var tokenCountResponse = await fetch('http://127.0.0.1:5000/get_token_count');
            var tokenCountData = await tokenCountResponse.json();
            console.log('tokenL', tokenCount)
            setTokenCount(tokenCountData.token_count);
         
    
          const dateTimeResponse = await fetch('http://127.0.0.1:5000/get_date_time');
          const dateTimeData = await dateTimeResponse.json();
          const formattedTime = formatTime(dateTimeData.relative_time_difference);
            setCurrentTime(formattedTime);
          } catch (error) {
          console.error('Error fetching data:', error);
        }
        };

    
        // Fetch data initially and set up interval for periodic updates
        fetchData();
        const intervalId = setInterval(fetchData, 60000); // Fetch every 1 minute
    
        // Clean up interval on component unmount
        return () => clearInterval(intervalId);
      }, []); // Run the effect only once on mount
    
  return (
    <div>
      <h2 className='title-monitor'>Token Monitoring Page</h2>
      <div className='ans-container'>
        <label htmlFor='modelDropDown'>Select Model: </label>
        <select id='modelDropDown' value={selectedModel} onChange={handleModelChange}>
            <option value="gpt-3.5-turbo">GPT-3.5-TURBO(FREE)</option>
            <option value="gpt-4">GPT-4(TIER 1)</option>
            <option value="text-embedding-ada-002">TEXT-EMBEDDING-ADA-002(FREE)</option>
            <option value="text-embedding-ada-002-T1">TEXT-EMBEDDING-ADA-002(TIER 1)</option>
        </select>

    <p className='title-mon'>Total Tokens Used: {tokenCount}</p>
    <p className='title-mon'>Token Limit (per minute): {limits[selectedModel]}</p>
    <p className='title-mon'>Relative Time (in Minute): {currentTime}</p>
    </div>
    </div>
  );
};

export default MonitoringComponent;
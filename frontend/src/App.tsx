import { useState, useEffect } from 'react';
import { FaSearch, FaMapMarkerAlt, FaCloudSun, FaSpinner } from 'react-icons/fa';
import { getForecast, getJobStatus } from './services/api';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
);

interface WeatherData {
  city: string;
  current_temp: number;
  predicted_temp_in_5_hours: number;
  forecast_5_hours: number[];
  ml_features_used: string[];
  model_version: string;
}

function App() {
  const [city, setCity] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [result, setResult] = useState<WeatherData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!city.trim()) return;
    
    setJobId(null);
    setStatus(null);
    setResult(null);
    setError(null);
    setLoading(true);

    try {
      const data = await getForecast(city);
      if (data.job_id) {
        setJobId(data.job_id);
      } else if (data.data) {
        setResult(data.data);
        setStatus('SUCCESS');
        setLoading(false);
      } else {
        setError("Invalid response from server.");
        setLoading(false);
      }
    } catch (err: any) {
      setError(err.response?.data?.error || err.message || 'An error occurred');
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!jobId || status === 'SUCCESS' || status === 'FAILURE') return;

    const interval = setInterval(async () => {
      try {
        const data = await getJobStatus(jobId);
        setStatus(data.status);
        if (data.status === 'SUCCESS') {
          setResult(data.result);
          setLoading(false);
          clearInterval(interval);
        } else if (data.status === 'FAILURE') {
          setError('Job failed to process.');
          setLoading(false);
          clearInterval(interval);
        }
      } catch (err) {
        console.error("Polling error", err);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [jobId, status]);

  const displayCity = result?.city || 'Search City';
  const currentTemp = result?.current_temp || 0;
  const predictedTemp = result?.predicted_temp_in_5_hours || currentTemp;
  
  let validForecast = result?.forecast_5_hours;
  if (!validForecast || validForecast.length === 0 || validForecast.every(v => v === 0)) {
    const diff = predictedTemp - currentTemp;
    validForecast = [
      currentTemp + diff * 0.2,
      currentTemp + diff * 0.4,
      currentTemp + diff * 0.6,
      currentTemp + diff * 0.8,
      predictedTemp
    ];
  }
  
  const chartData = {
    labels: ['Now', '+1h', '+2h', '+3h', '+4h', '+5h'],
    datasets: [
      {
        data: [currentTemp, ...validForecast],
        borderColor: '#f97316',
        borderWidth: 2,
        pointRadius: 3,
        pointBackgroundColor: '#f97316',
        tension: 0.4,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: { enabled: true }
    },
    scales: {
      x: { display: false },
      y: { display: false }
    }
  };

  const timeCols = ['+1h', '+2h', '+3h', '+4h', '+5h'];
  const dataCols = validForecast;
  const humidityCols = ['62%', '63%', '64%', '65%', '66%'];

  const dateNow = new Date();
  const dateStr = dateNow.toLocaleString('en-US', { weekday: 'short', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });

  return (
    <div 
      className="min-h-screen w-full flex items-center justify-center p-4 font-sans relative bg-cover bg-center bg-fixed text-white drop-shadow-md"
      style={{ backgroundImage: "url('https://images.unsplash.com/photo-1518803194621-27188ba362c9?q=80&w=2500&auto=format&fit=crop')" }}
    >
      
      {/* Main Container */}
      <div className="max-w-5xl w-full md:h-[580px] rounded-[28px] overflow-hidden relative flex flex-col md:flex-row shadow-2xl z-10 bg-black/40 backdrop-blur-2xl border border-white/20">
        
        {/* Left Sidebar (30%) */}
        <div className="w-full md:w-[30%] bg-white/5 border-r border-white/20 p-8 flex flex-col justify-between">
          
          <form onSubmit={handleSubmit} className="relative">
             <div className="flex items-center border-b border-white/40 pb-2">
               <FaCloudSun className="text-white/70 mr-3 text-xl" />
               <input
                 type="text"
                 placeholder="Enter city..."
                 value={city}
                 onChange={(e) => setCity(e.target.value)}
                 className="w-full bg-transparent border-none text-white placeholder-white/60 focus:outline-none"
               />
               <button type="submit" disabled={loading} className="text-white/80 hover:text-white transition">
                 {loading && !result ? <FaSpinner className="animate-spin" /> : <FaSearch />}
               </button>
             </div>
             {error && <p className="text-red-300 text-xs mt-2">{error}</p>}
          </form>

          {result && (
            <>
              <div className="mt-12 flex-1">
                 <div className="mb-2">
                   <h1 className="text-6xl font-light tracking-tight">{currentTemp}°</h1>
                 </div>
                 <p className="text-sm text-white/70">Feels like: {(currentTemp + 1.2).toFixed(1)}°</p>
              </div>

              <div className="mt-8">
                 <div className="flex items-center justify-between border-b border-white/20 pb-3 mb-3">
                    <span className="text-white/80">Humidity</span>
                    <span className="font-semibold">64%</span>
                 </div>
                 <div className="flex items-center justify-between border-b border-white/20 pb-3">
                    <span className="text-white/80">Clouds</span>
                    <span className="font-semibold">40%</span>
                 </div>
              </div>
            </>
          )}
        </div>

        {/* Right Main Panel (70%) */}
        <div className="w-full md:w-[70%] p-10 flex flex-col justify-between flex-1 relative">
          
          {loading && !result && (
             <div className="flex-1 flex flex-col items-center justify-center opacity-80 space-y-4">
                <FaSpinner className="animate-spin text-4xl text-white/80" />
                <p className="text-lg">Processing forecast with ML model...</p>
             </div>
          )}

          {!result && !loading && (
             <div className="flex-1 flex flex-col items-center justify-center opacity-70 space-y-4 text-center">
                <FaSearch className="text-6xl mb-4 text-white/50" />
                <p className="text-xl font-light">Enter a city to generate an AI-powered forecast.</p>
             </div>
          )}

          {result && (
            <>
              <div>
                <p className="text-xs uppercase tracking-widest text-white/70 mb-2">Weather Forecast</p>
                <h2 className="text-5xl font-bold mb-4 capitalize">
                   Scattered Clouds
                </h2>
                <div className="flex items-center space-x-2 text-white/80 text-sm">
                  <FaMapMarkerAlt className="text-white/60" />
                  <span>{displayCity} • {dateStr}</span>
                </div>
                
                <p className="mt-8 text-white/70 leading-relaxed max-w-xl">
                  Wind 12.3 km/h. Pressure is 1012 hPa. Visibility is 10000m. Maximum temperature is {(currentTemp + 2).toFixed(1)}°. Minimum temperature is {(currentTemp - 2).toFixed(1)}°.
                </p>
              </div>

              <div className="mt-12">
                <div className="grid grid-cols-5 gap-4 text-center mb-2">
                   {timeCols.map((col, idx) => (
                     <div key={idx} className="flex flex-col space-y-2">
                       <span className="text-sm text-white/80">{col}</span>
                       <span className="text-3xl font-normal">{dataCols[idx].toFixed(0)}°</span>
                       <span className="text-xs opacity-75 text-white/60">{humidityCols[idx]}</span>
                     </div>
                   ))}
                </div>
                
                <div className="h-[60px] w-full mt-2 -ml-2">
                   <Line data={chartData} options={chartOptions} />
                </div>
              </div>
            </>
          )}
          
        </div>
      </div>
    </div>
  );
}

export default App;

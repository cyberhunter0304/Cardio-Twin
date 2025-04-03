import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Heart, Activity, Droplets, Zap, Github, Gauge } from 'lucide-react';
import { Line } from 'react-chartjs-2';
import { HeartScene } from './components/HeartScene';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface UserData {
  age: string;
  sex: string;
  cp: string;
  fbs: string;
  restecg: string;
  slope: string;
}

interface SimulationData {
  thalach: number;    // Heart Rate
  chol: number;       // Cholesterol
  oldpeak: number;    // ST Depression
  trestbps: number;   // Blood Pressure
  exang: number;      // Exercise induced angina
  prediction: string; // Risk prediction
}

function App() {
  const [userData, setUserData] = useState<UserData>({
    age: '',
    sex: '',
    cp: '',
    fbs: '0',        // Default values as per backend
    restecg: '0',    // Default values as per backend
    slope: '1',      // Default values as per backend
  });

  const [data, setData] = useState<SimulationData>({
    thalach: 0,
    chol: 0,
    oldpeak: 0,
    trestbps: 0,
    exang: 0,
    prediction: 'Waiting...',
  });

  const [history, setHistory] = useState<SimulationData[]>([]);
  const [simulationStarted, setSimulationStarted] = useState(false);
  const [exerciseIntensity, setExerciseIntensity] = useState(50);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setUserData({ ...userData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await axios.post("http://localhost:5000/start", userData);
      setSimulationStarted(true);
    } catch (error) {
      console.error("Error starting simulation:", error);
    }
  };

  useEffect(() => {
    if (!simulationStarted) return;

    const fetchData = async () => {
      try {
        const response = await axios.get(`http://localhost:5000/prediction?intensity=${exerciseIntensity}`);
        const newData = response.data;
        setData(newData);
        setHistory(prev => [...prev.slice(-19), newData]);
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    };

    const interval = setInterval(fetchData, 1000);
    return () => clearInterval(interval);
  }, [simulationStarted, exerciseIntensity]);

  const chartData = {
    labels: history.map((_, index) => `${index + 1}s`),
    datasets: [
      {
        label: 'Heart Rate',
        data: history.map(h => h.thalach),
        borderColor: '#8F87F1',
        backgroundColor: '#8F87F122',
        tension: 0.4,
        fill: true,
      },
      {
        label: 'Blood Pressure',
        data: history.map(h => h.trestbps),
        borderColor: '#C68EFD',
        backgroundColor: '#C68EFD22',
        tension: 0.4,
        fill: true,
      },
    ],
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      {/* Navbar */}
      <nav className="bg-white shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <a 
              href="https://mjonathan.uno" 
              target="_blank" 
              rel="noopener noreferrer" 
              className="flex items-center space-x-2 hover:opacity-80 transition-opacity"
            >
              <Heart className="h-6 w-6 text-[#8F87F1]" />
              <span className="text-xl font-bold gradient-text">Cardio Twin</span>
            </a>
            <div className="flex items-center space-x-4">
              <a 
                href="https://github.com/cyberhunter0304" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="text-gray-600 hover:text-[#8F87F1] transition-colors"
              >
                <Github className="h-5 w-5" />
              </a>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      {!simulationStarted && (
        <div className="hero-gradient py-20 text-white">
          <div className="container mx-auto px-4 text-center">
            <h1 className="text-4xl md:text-5xl font-bold mb-6">Real-time Heart Monitoring</h1>
            <p className="text-lg md:text-xl mb-8 opacity-90">
              Experience advanced cardiac simulation with our cutting-edge monitoring system
            </p>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-grow container mx-auto px-4 py-8">
        <div className="bg-white rounded-xl shadow-xl p-6 mb-8">
          {!simulationStarted ? (
            <form onSubmit={handleSubmit} className="max-w-2xl mx-auto space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Age (Years)</label>
                  <input
                    type="number"
                    name="age"
                    value={userData.age}
                    onChange={handleChange}
                    min="0"
                    className="mt-1 block w-full rounded-lg border-gray-200 shadow-sm focus:border-[#8F87F1] focus:ring focus:ring-[#8F87F1] focus:ring-opacity-50"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Sex</label>
                  <select
                    name="sex"
                    value={userData.sex}
                    onChange={handleChange}
                    className="mt-1 block w-full rounded-lg border-gray-200 shadow-sm focus:border-[#8F87F1] focus:ring focus:ring-[#8F87F1] focus:ring-opacity-50"
                  >
                    <option value="">Select</option>
                    <option value="1">Male</option>
                    <option value="0">Female</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Chest Pain Type</label>
                  <select
                    name="cp"
                    value={userData.cp}
                    onChange={handleChange}
                    className="mt-1 block w-full rounded-lg border-gray-200 shadow-sm focus:border-[#8F87F1] focus:ring focus:ring-[#8F87F1] focus:ring-opacity-50"
                  >
                    <option value="">Select</option>
                    <option value="0">Typical Angina</option>
                    <option value="1">Atypical Angina</option>
                    <option value="2">Non-Anginal Pain</option>
                    <option value="3">Asymptomatic</option>
                  </select>
                </div>
              </div>
              
              <button
                type="submit"
                className="w-full py-3 px-4 rounded-lg text-white font-medium bg-gradient-to-r from-[#8F87F1] to-[#C68EFD] hover:opacity-90 transition duration-200 shadow-lg"
              >
                Start Simulation
              </button>
            </form>
          ) : (
            <div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                <div className="space-y-6">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gradient-to-br from-[#8F87F1] to-[#C68EFD] p-6 rounded-lg text-white shadow-lg">
                      <div className="flex items-center mb-2">
                        <Heart className="mr-2" />
                        <h3 className="text-lg font-semibold">Heart Rate</h3>
                      </div>
                      <p className="text-3xl font-bold">{data.thalach} BPM</p>
                    </div>
                    
                    <div className="bg-gradient-to-br from-[#C68EFD] to-[#E9A5F1] p-6 rounded-lg text-white shadow-lg">
                      <div className="flex items-center mb-2">
                        <Droplets className="mr-2" />
                        <h3 className="text-lg font-semibold">Cholesterol</h3>
                      </div>
                      <p className="text-3xl font-bold">{data.chol} mg/dL</p>
                    </div>
                    
                    <div className="bg-gradient-to-br from-[#E9A5F1] to-[#FED2E2] p-6 rounded-lg text-white shadow-lg">
                      <div className="flex items-center mb-2">
                        <Zap className="mr-2" />
                        <h3 className="text-lg font-semibold">ST Depression</h3>
                      </div>
                      <p className="text-3xl font-bold">{data.oldpeak}</p>
                    </div>
                    
                    <div className="bg-gradient-to-br from-[#FED2E2] to-[#8F87F1] p-6 rounded-lg text-white shadow-lg">
                      <div className="flex items-center mb-2">
                        <Activity className="mr-2" />
                        <h3 className="text-lg font-semibold">Blood Pressure</h3>
                      </div>
                      <p className="text-3xl font-bold">{data.trestbps} mmHg</p>
                    </div>
                  </div>

                  <div className="bg-white p-6 rounded-lg shadow-lg border border-gray-100">
                    <div className="flex items-center justify-between mb-6">
                      <h3 className="text-xl font-semibold gradient-text">Risk Assessment</h3>
                      <span className={`px-4 py-2 rounded-full text-white font-medium ${
                        data.prediction === 'High Risk' 
                          ? 'bg-red-500' 
                          : data.prediction === 'Low Risk'
                          ? 'bg-green-500'
                          : 'bg-gray-500'
                      }`}>
                        {data.prediction}
                      </span>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <Gauge className="h-5 w-5 text-[#8F87F1] mr-2" />
                          <span className="text-sm font-medium text-gray-700">Exercise Intensity</span>
                        </div>
                        <span className="text-sm font-medium text-[#8F87F1]">{exerciseIntensity}%</span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={exerciseIntensity}
                        onChange={(e) => setExerciseIntensity(Number(e.target.value))}
                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-[#8F87F1]"
                      />
                    </div>
                  </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow-lg border border-gray-100">
                  <h3 className="text-xl font-semibold mb-4 gradient-text">3D Heart Visualization</h3>
                  <HeartScene heartRate={data.thalach} />
                </div>
              </div>
              
              <div className="bg-white p-6 rounded-lg shadow-lg border border-gray-100">
                <h3 className="text-xl font-semibold mb-4 gradient-text">Real-time Monitoring</h3>
                <Line data={chartData} options={{
                  responsive: true,
                  plugins: {
                    legend: {
                      position: 'top' as const,
                    },
                    title: {
                      display: true,
                      text: 'Heart Rate & Blood Pressure Trends',
                      color: '#8F87F1'
                    }
                  },
                  scales: {
                    y: {
                      grid: {
                        color: '#E9A5F122',
                      }
                    },
                    x: {
                      grid: {
                        color: '#E9A5F122',
                      }
                    }
                  }
                }} />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-100 py-6">
        <div className="container mx-auto px-4 text-center">
          <p className="text-gray-600">
            Made with 💜 by{' '}
            <a 
              href="https://mjonathan.uno" 
              target="_blank" 
              rel="noopener noreferrer" 
              className="text-[#8F87F1] hover:text-[#C68EFD] transition-colors font-medium"
            >
              Jonathan
            </a>
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
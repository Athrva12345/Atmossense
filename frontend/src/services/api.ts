import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/',
});

export const getForecast = async (city: string) => {
  // Using GET to match the backend implementation of ForecastAPIView
  const response = await api.get('/forecast/', { params: { city } });
  return response.data;
};

export const getJobStatus = async (jobId: string) => {
  const response = await api.get(`/jobs/${jobId}/`);
  return response.data;
};

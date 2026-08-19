import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/',
});

export const getForecast = async (city: string, signal?: AbortSignal) => {
  // Using GET to match the backend implementation of ForecastAPIView
  const response = await api.get('/forecast/', { params: { city }, signal });
  return response.data;
};

export const getJobStatus = async (jobId: string, signal?: AbortSignal) => {
  const response = await api.get(`/jobs/${jobId}/`, { signal });
  return response.data;
};

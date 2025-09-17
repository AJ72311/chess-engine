import axios from 'axios';

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

const apiClient = axios.create({
    baseURL: apiBaseUrl,
});

export default apiClient;
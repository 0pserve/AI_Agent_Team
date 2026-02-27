import axios, { AxiosInstance } from 'axios';
import { ProjectRequest, TaskStatus } from './types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  async checkHealth(): Promise<{ status: string }> {
    const response = await this.client.get('/health');
    return response.data;
  }

  async executeProject(request: ProjectRequest): Promise<TaskStatus> {
    const response = await this.client.post('/api/execute', request);
    return response.data;
  }

  async getTaskStatus(taskId: string): Promise<TaskStatus> {
    const response = await this.client.get(`/api/tasks/${taskId}`);
    return response.data;
  }

  async listTasks(): Promise<TaskStatus[]> {
    const response = await this.client.get('/api/tasks');
    return response.data;
  }

  async deleteTask(taskId: string): Promise<void> {
    await this.client.delete(`/api/tasks/${taskId}`);
  }
}

export const apiService = new ApiService();
export default apiService;

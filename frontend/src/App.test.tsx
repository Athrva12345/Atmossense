import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from './App';
import * as api from './services/api';
import { vi, describe, it, expect, beforeEach } from 'vitest';

// Mock the API module
vi.mock('./services/api', () => ({
  getForecast: vi.fn(),
  getJobStatus: vi.fn(),
}));

describe('App Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('transitions from PENDING (skeleton) to SUCCESS (forecast view)', async () => {
    // Mock getForecast to return a jobId
    (api.getForecast as any).mockResolvedValue({ job_id: '123' });
    
    // Mock getJobStatus to first return PENDING, then SUCCESS
    (api.getJobStatus as any)
      .mockResolvedValueOnce({ status: 'PENDING' })
      .mockResolvedValueOnce({
        status: 'SUCCESS',
        result: {
          city: 'London',
          current_temp: 15,
          predicted_temp_in_5_hours: 18,
          forecast_5_hours: [15, 16, 17, 18, 18],
          ml_features_used: ['temp'],
          model_version: 'v1.0'
        }
      });

    render(<App />);

    // Type in search box and submit
    const input = screen.getByPlaceholderText('Enter city...');
    fireEvent.change(input, { target: { value: 'London' } });
    
    const submitButton = screen.getByTestId('search-button');
    fireEvent.click(submitButton);

    // Verify PENDING UI state
    expect(await screen.findByTestId('pending-state')).toBeInTheDocument();
    
    // Verify SUCCESS UI state displays eventually (using waitFor for polling simulation)
    await waitFor(() => {
      expect(screen.getByText('London', { exact: false })).toBeInTheDocument();
    }, { timeout: 3000 });

    // Verify model version pill
    expect(screen.getByTestId('model-version')).toHaveTextContent('Model: v1.0');
  });

  it('renders HTTP 429 rate limit error UI', async () => {
    // Mock getForecast to throw a 429 error
    const error429 = {
      response: { status: 429 }
    };
    (api.getForecast as any).mockRejectedValue(error429);

    render(<App />);

    const input = screen.getByPlaceholderText('Enter city...');
    fireEvent.change(input, { target: { value: 'New York' } });
    
    const submitButton = screen.getByTestId('search-button');
    fireEvent.click(submitButton);

    // Verify rate limit UI displays
    expect(await screen.findByTestId('rate-limit-error')).toBeInTheDocument();
    expect(screen.getByText('Whoa, slow down!')).toBeInTheDocument();
  });
});

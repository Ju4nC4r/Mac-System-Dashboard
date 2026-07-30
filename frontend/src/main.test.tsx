import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { App } from './main'

const overview = { timestamp: 1, cpu: { percentage: 23, load: 1.2, cores: 8 }, memory: { total: 8_000_000_000, used: 4_000_000_000, available: 4_000_000_000, percentage: 50 }, disk: { total: 100_000_000_000, used: 60_000_000_000, free: 40_000_000_000, percentage: 60 }, battery: { available: true, percentage: 80, charging: true } }
const processes = [{ pid: 100, name: 'Safari', cpu: 5, memory: 200_000_000, state: 'S' }, { pid: 200, name: 'Terminal', cpu: 2, memory: 100_000_000, state: 'R' }]

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn((url: string) => Promise.resolve({ json: () => Promise.resolve(url === '/api/overview' ? overview : url === '/api/history' ? [overview] : processes) })))
})

describe('dashboard', () => {
  it('renders live metric cards and filters processes', async () => {
    render(<App />)
    expect(await screen.findByText('23%')).toBeTruthy()
    expect(screen.getByText('Safari')).toBeTruthy()
    fireEvent.change(screen.getByPlaceholderText('Buscar proceso'), { target: { value: 'Terminal' } })
    await waitFor(() => expect(screen.getByText('Terminal')).toBeTruthy())
    expect(screen.queryByText('Safari')).toBeNull()
  })
})

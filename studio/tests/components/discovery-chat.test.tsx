import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { DiscoveryChat } from '@/components/discovery/discovery-chat';

const originalScrollTo = HTMLElement.prototype.scrollTo;
beforeEach(() => { HTMLElement.prototype.scrollTo = vi.fn(); });
afterEach(() => { cleanup(); HTMLElement.prototype.scrollTo = originalScrollTo; vi.unstubAllGlobals(); });

describe('DiscoveryChat text-stream contract', () => {
  it('renders and extracts plain text split across arbitrary UTF-8 and line boundaries', async () => {
    const content = 'Source: München\nkpi_id: KPI-COM-005\nname: Net sales';
    const bytes = new TextEncoder().encode(content);
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        // Deliberately split every byte, including the multi-byte ü character.
        for (let index = 0; index < bytes.length; index += 1) controller.enqueue(bytes.slice(index, index + 1));
        controller.close();
      },
    });
    const fetchMock = vi.fn().mockResolvedValue(new Response(stream, { headers: { 'Content-Type': 'text/plain; charset=utf-8' } }));
    vi.stubGlobal('fetch', fetchMock);
    const onExtract = vi.fn();
    render(<DiscoveryChat context="Source evidence" onExtract={onExtract} />);
    fireEvent.change(screen.getByRole('textbox', { name: 'Discovery question' }), { target: { value: 'Extract candidates' } });
    fireEvent.click(screen.getByRole('button', { name: 'Send' }));
    await waitFor(() => expect(onExtract).toHaveBeenCalledWith(content));
    expect(screen.getByText(/Source: München/).textContent).toBe(content);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [, request] = fetchMock.mock.calls[0];
    expect(JSON.parse(request.body).context).toBe('Source evidence');
  });

  it('shows structured request errors as readable text', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ error: { message: 'Authentication required' } }), { status: 401 })));
    const onExtract = vi.fn();
    render(<DiscoveryChat context="" onExtract={onExtract} />);
    fireEvent.change(screen.getByRole('textbox', { name: 'Discovery question' }), { target: { value: 'Extract candidates' } });
    fireEvent.click(screen.getByRole('button', { name: 'Send' }));
    await screen.findByText('Error: Authentication required');
    expect(onExtract).not.toHaveBeenCalled();
  });
});

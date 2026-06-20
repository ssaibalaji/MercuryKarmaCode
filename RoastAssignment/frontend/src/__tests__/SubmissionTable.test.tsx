import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { ChakraProvider } from '@chakra-ui/react';
import { SubmissionTable } from '../components/submissions/SubmissionTable';
import { Submission } from '../types';

function renderTable(submissions: Submission[]) {
  return render(
    <ChakraProvider>
      <MemoryRouter>
        <SubmissionTable submissions={submissions} />
      </MemoryRouter>
    </ChakraProvider>
  );
}

const baseSubmissions: Submission[] = [
  {
    id: 1,
    userId: 10,
    studentName: 'Alice Adams',
    studentEmail: 'alice@example.com',
    assignmentName: 'Assignment 1',
    githubRepoUrl: 'https://github.com/alice/repo',
    syncStatus: 'synced',
    submittedAt: '2026-06-01T10:00:00Z',
  },
  {
    id: 2,
    userId: 11,
    studentName: 'Bob Brown',
    studentEmail: 'bob@example.com',
    assignmentName: 'Assignment 2',
    githubRepoUrl: 'https://github.com/bob/repo',
    syncStatus: 'pending',
    submittedAt: '2026-06-02T10:00:00Z',
  },
  {
    id: 3,
    userId: 12,
    studentName: 'Carla Cruz',
    studentEmail: 'carla@example.com',
    assignmentName: 'Assignment 3',
    githubRepoUrl: 'https://github.com/carla/repo',
    syncStatus: 'error',
    submittedAt: '2026-06-03T10:00:00Z',
  },
];

describe('SubmissionTable', () => {
  it('renders a "no submissions" message for an empty list', () => {
    renderTable([]);
    expect(screen.getByText(/no submissions found/i)).toBeInTheDocument();
  });

  it('renders a row for each submission with student name and assignment', () => {
    renderTable(baseSubmissions);

    expect(screen.getByText('Alice Adams')).toBeInTheDocument();
    expect(screen.getByText('Assignment 1')).toBeInTheDocument();
    expect(screen.getByText('Bob Brown')).toBeInTheDocument();
    expect(screen.getByText('Assignment 2')).toBeInTheDocument();
    expect(screen.getByText('Carla Cruz')).toBeInTheDocument();
    expect(screen.getByText('Assignment 3')).toBeInTheDocument();
  });

  it('renders a distinctly colored badge per sync_status', () => {
    // Chakra resolves `colorScheme` into emotion-generated (hashed) class
    // names rather than literal "green"/"yellow"/"red" strings, so we can't
    // assert on className text. Instead assert each status renders its own
    // `chakra-badge` element and that the three statuses don't collapse onto
    // identical computed background colors (i.e. the colorScheme prop is
    // actually wired per-status, per SYNC_STATUS_COLOR in SubmissionTable.tsx).
    renderTable(baseSubmissions);

    const syncedBadge = screen.getByText('synced');
    const pendingBadge = screen.getByText('pending');
    const errorBadge = screen.getByText('error');

    [syncedBadge, pendingBadge, errorBadge].forEach((badge) => {
      expect(badge).toHaveClass('chakra-badge');
    });

    const syncedColor = getComputedStyle(syncedBadge).backgroundColor;
    const pendingColor = getComputedStyle(pendingBadge).backgroundColor;
    const errorColor = getComputedStyle(errorBadge).backgroundColor;

    expect(syncedColor).not.toEqual(pendingColor);
    expect(syncedColor).not.toEqual(errorColor);
    expect(pendingColor).not.toEqual(errorColor);
  });
});

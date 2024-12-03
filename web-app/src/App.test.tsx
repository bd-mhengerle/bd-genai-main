import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom/extend-expect';
import App from './App';

test('renders learn react link', () => {
  render(<div data-testid="header-component"/>);
  const headerElement = screen.getByTestId('header-component');
  expect(headerElement).toBeInTheDocument();
});
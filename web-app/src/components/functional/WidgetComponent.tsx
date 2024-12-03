import React from 'react';
import styled from 'styled-components';
import { FaInfoCircle } from 'react-icons/fa'; // Example for the info icon

// Styled components for the widget
const WidgetContainer = styled.div<{ isNegative: boolean }>`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-around;
  padding: 16px;
  border: 3px solid ${(props) => (props.isNegative ? 'var(--negative-card-border)' : 'var(--positive-card-border)')};
  border-radius: 8px;
  width: 250px;
  height: 120px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);  // Soft shadow
  box-sizing: border-box;
  background: ${(props) => (props.isNegative ? 'var(--negative-card)' : 'var(--positive-card)')};
`;

const Value = styled.h2`
  margin: 0;
  font-size: 24px;
  color: var(--font-color);
`;

const LabelContainer = styled.div`
  display: flex;
  align-items: center;
  font-size: 14px;
  color: #555;
  gap: 4px;
`;

const Label = styled.span`
  margin-left: 8px;
`;

const ChangeContainer = styled.div<{ isNegative: boolean }>`
  display: flex;
  align-items: center;
  font-size: 12px;
  color: ${(props) => (props.isNegative ? '#d9534f' : '#5cb85c')}; // Red for negative, green for positive
`;

const Arrow = styled.span`
  font-size: 14px;
  margin-right: 4px;
`;

const PercentageChange = styled.span``;

const Widget = ({ value, label, isNegative, percentageChange }: 
    { value: number, label: string, isNegative: boolean, percentageChange: number }) => {
  return (
    <WidgetContainer isNegative={false}>
      <Value>{value}</Value>
      <LabelContainer>
        <Label>{label}</Label>
        <FaInfoCircle />
      </LabelContainer>
      {/* <ChangeContainer isNegative={isNegative}>
        <Arrow>{isNegative ? '▼' : '▲'}</Arrow>
        <PercentageChange>{percentageChange}% vs Prior YTD</PercentageChange>
      </ChangeContainer> */}
    </WidgetContainer>
  );
};

export default Widget;
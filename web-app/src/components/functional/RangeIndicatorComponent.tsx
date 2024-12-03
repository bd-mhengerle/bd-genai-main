import React from 'react';
import styled from 'styled-components';

// Styled container for the range indicator
const RangeContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 32px;
  padding: 20px;
`;

const RangeItem = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
`;

// Styled circle with dynamic color
const Circle = styled.div`
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 3px solid ${(props) => props.color};
`;

// Label for each range item
const Label = styled.span`
  font-size: 14px;
  color: #333;
`;

const RangeIndicator = () => {
  return (
    <RangeContainer>
      <RangeItem>
        <Circle color="#FF8880" />
        <Label>Above Range</Label>
      </RangeItem>
      <RangeItem>
        <Circle color="#6c757d" />
        <Label>Within Range</Label>
      </RangeItem>
      <RangeItem>
        <Circle color="#00E893" />
        <Label>Below Range</Label>
      </RangeItem>
    </RangeContainer>
  );
};

export default RangeIndicator;
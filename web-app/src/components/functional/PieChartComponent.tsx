import React from 'react';
import styled from 'styled-components';
import { PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';

// Sample data for the chart
const data = [
  { name: '50Mb - 100Mb', value: 30, color: '#003f5c' },
  { name: '25Mb - 50Mb', value: 20, color: '#58508d' },
  { name: '10Mb - 25Mb', value: 15, color: '#bc5090' },
  { name: '1Mb - 10Mb', value: 10, color: '#ff6361' },
  { name: '0Mb - 1Mb', value: 25, color: '#ffa600' },
];

// Styled components for the chart container
const ChartContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 20px;
  width: 360px;
`;

const CenteredLabel = styled.div`
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 24px;
  font-weight: bold;
  text-align: center;

  & span {
    display: block;
    font-size: 14px;
    color: #888;
  }
`;

const DocumentFileSizeChart = () => {
  const totalSize = '2.78 Tb';

  return (
    <ChartContainer>
      <h5>Document File Size</h5>
      <div className='d-flex flex-row align-items-center justify-content-center'>
        <div style={{ position: 'relative', width: 250, height: 250 }}>
            <PieChart width={250} height={250}>
            <Pie
                data={data}
                dataKey="value"
                cx="50%"
                cy="50%"
                innerRadius={70}
                outerRadius={100}
                fill="#8884d8"
                paddingAngle={3}
                isAnimationActive={false}
            >
                {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
            </Pie>
            <Tooltip />
            </PieChart>
            {/* Centered Label for total size */}
            <CenteredLabel>
            {totalSize}
            <span>Tb</span>
            </CenteredLabel>
        </div>
        {/* Custom legend */}
        <ul style={{ listStyleType: 'none', padding: 0 }}>
            {data.map((entry, index) => (
            <li key={index} style={{ color: entry.color }}>
                <span
                style={{
                    display: 'inline-block',
                    width: '6px',
                    height: '6px',
                    backgroundColor: entry.color,
                    marginRight: '10px',
                }}
                />
                {entry.name}
            </li>
            ))}
        </ul>
      </div>
    </ChartContainer>
  );
};

export default DocumentFileSizeChart;
import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

// Sample data for the chart
const data = [
  { date: 'Jan 1', bcFees: 60, newChats: 65, resumedChats: 70, docsUploaded: 80, generatedQuestions: 85 },
  { date: 'Feb 1', bcFees: 65, newChats: 60, resumedChats: 75, docsUploaded: 82, generatedQuestions: 87 },
  { date: 'Mar 1', bcFees: 70, newChats: 68, resumedChats: 72, docsUploaded: 78, generatedQuestions: 80 },
  { date: 'Apr 1', bcFees: 75, newChats: 75, resumedChats: 80, docsUploaded: 83, generatedQuestions: 90 },
  { date: 'May 1', bcFees: 80, newChats: 80, resumedChats: 85, docsUploaded: 85, generatedQuestions: 92 },
  { date: 'Jun 1', bcFees: 85, newChats: 88, resumedChats: 90, docsUploaded: 90, generatedQuestions: 95 },
  { date: 'Jul 1', bcFees: 82, newChats: 83, resumedChats: 88, docsUploaded: 87, generatedQuestions: 89 },
  { date: 'Aug 1', bcFees: 78, newChats: 80, resumedChats: 85, docsUploaded: 84, generatedQuestions: 87 },
  { date: 'Sep 1', bcFees: 90, newChats: 92, resumedChats: 95, docsUploaded: 98, generatedQuestions: 100 },
  { date: 'Oct 1', bcFees: 88, newChats: 85, resumedChats: 88, docsUploaded: 90, generatedQuestions: 95 },
  { date: 'Nov 1', bcFees: 85, newChats: 82, resumedChats: 85, docsUploaded: 87, generatedQuestions: 90 },
];

const CustomLineChart = () => {
  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis domain={[60, 110]} tickFormatter={(value) => `${value}%`} />
        <Tooltip />
        <Legend />
        
        <Line
          type="monotone"
          dataKey="bcFees"
          stroke="#000000"
          strokeWidth={2}
          dot={false}
          name="BC Fees"
        />
        <Line
          type="monotone"
          dataKey="newChats"
          stroke="#8884d8"
          strokeDasharray="3 3"
          dot={false}
          name="New Chats"
        />
        <Line
          type="monotone"
          dataKey="resumedChats"
          stroke="#82ca9d"
          strokeDasharray="5 5"
          dot={false}
          name="Resumed Chats"
        />
        <Line
          type="monotone"
          dataKey="docsUploaded"
          stroke="#ffc658"
          strokeDasharray="7 7"
          dot={false}
          name="Documents Uploaded"
        />
        <Line
          type="monotone"
          dataKey="generatedQuestions"
          stroke="#ff7300"
          strokeDasharray="8 4"
          dot={false}
          name="Generated Questions Asked"
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default CustomLineChart;
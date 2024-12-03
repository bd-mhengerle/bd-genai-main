import React, { useEffect, useRef, useState } from "react";
import styled from "styled-components";
import { Select } from "../ui/Select";
import { AiOutlineSearch } from "react-icons/ai";
import { useStateContext } from "../../StateContext";
import Widget from "./WidgetComponent";
import { Reg_16, Reg_24 } from "../styling/typography";
import RangeIndicator from "./RangeIndicatorComponent";
import LineChartComponent from "./LineChartComponent";
import DocumentFileSizeChart from "./PieChartComponent";
import { useQueries, useQuery, useQueryClient } from "react-query";
import { getNewChats, getNewKbs, getNewMsgs, getNewUploads, getResumedChats, getUserActivity } from "../../api/api";
import { ApiResponse } from "../../models/ApiResponse";
import { UserActivityInfo } from "../../api/model";

interface ButtonProps {
  backgroundColor?: string;
  hoverColor?: string;
}

const FiltersContainer = styled.div`
  display: flex;
  gap: 1rem;
  justify-content: space-around;
  align-items: center;
  padding: 10px;
  background-color: #f4f4f4;
  border-radius: 8px;
`;

const DashboardContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
`;

const ActivityContainer = styled.div`
  display: flex;
  flex-direction: column;
  background-color: var(--background);
  gap: 16px;
  width: 100%;
  padding: 16px;
`;

const SideContainer = styled.div`
  display: flex;
  flex-direction: column;
  background-color: #ffffff;
  gap: 25px;
  padding: 16px;
`;

const ActivityDetailsContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 10px;
  height: 800px;
  overflow: auto;
`;

const SearchContainer = styled.div`
  display: flex;
  align-items: center;
  background-color: white;
  border-radius: 8px;
  padding: 4px 10px;
  width: 100%;
  max-width: 200px;
`;

const SearchInput = styled.input`
  border: none;
  outline: none;
  padding: 8px;
  width: 100%;
  font-size: 16px;
  border-radius: 8px;
`;

const TableWrapper = styled.div`
  width: 100%;
  max-height: 600px;
  overflow: auto;
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
`;

const Thead = styled.thead`
  background-color: var(--background-hover);
  position: sticky;
  top: 0;
  z-index: 0;
`;

const Th = styled.th`
  padding: 12px 15px;
  border: 1px solid #ddd;
  text-align: left;
  font-weight: bold;
  font-size: 14px;
`;

const Td = styled.td`
  padding: 12px 15px;
  border: 1px solid #ddd;
  text-align: left;
  font-size: 14px;
`;

const Tr = styled.tr`
  &:nth-child(even) {
    background-color: var(--background-hover);
  }
`;

const Checkbox = styled.input.attrs({ type: "checkbox" })`
  margin: 0;
`;

const ButtonContainer = styled.div`
  display: flex;
  justify-content: space-between;
  padding: 10px;
  background-color: #cde9f4;
`;

const ClassManagementButton = styled.button<ButtonProps>`
  padding: 8px 20px;
  background-color: ${(props) => props.backgroundColor || "#0a67b3"};
  color: ${(props) => props.color || "var(--font-color)"};
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;

  &:hover {
    background-color: ${(props) => props.hoverColor || "#084f8d"};
  }
`;

interface TableComponentProps {
  headers: string[];
  data: any[];
  indexed: boolean;
}

const TableComponent: React.FC<TableComponentProps> = ({ headers, data, indexed }) => {
  const [sortConfig, setSortConfig] = useState<{ key: string, direction: string } | null>(null);

  // Columns to display with proper mapping
  const columnsToDisplay: Record<string, string> = {
    "email": "Email",
    "name": "Name",
    "newChat": "New Chat",
    "questionsAsked": "Questions Asked",
    "chatsResumed": "Chats Resumed",
    "documentsUploaded": "Documents Uploaded",
    "knowledgeBaseCreated": "Knowledge Base Created",
    "lastMessageAt": "Last Message At"
  };

  // Filter headers to only include columnsToDisplay keys
  const filteredHeaders = headers.filter(header => Object.keys(columnsToDisplay).includes(header));

  const handleSort = (header: string) => {
    let direction = "ascending";
    if (sortConfig && sortConfig.key === header && sortConfig.direction === "ascending") {
      direction = "descending";
    }
    setSortConfig({ key: header, direction });
  };

  // Format date to user's local time
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString(undefined, {
      year: 'numeric',
      month: 'numeric',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  // Filter and sort data based on the sortConfig
  const sortedData = React.useMemo(() => {
    if (!sortConfig || !data) return data;
    return [...data].sort((a, b) => {
      const aVal = a[sortConfig.key];
      const bVal = b[sortConfig.key];
      if (aVal < bVal) return sortConfig.direction === "ascending" ? -1 : 1;
      if (aVal > bVal) return sortConfig.direction === "ascending" ? 1 : -1;
      return 0;
    });
  }, [data, sortConfig]);

  return (
    <TableWrapper>
      <Table>
        <Thead>
          <Tr>
            <Th>{indexed ? "▼" : <Checkbox />}</Th>
            {Object.keys(columnsToDisplay).map((header, index) => (
              filteredHeaders.includes(header) && (
                <Th key={index} onClick={() => handleSort(header)}>
                  {columnsToDisplay[header]}{" "}
                  {sortConfig?.key === header ? (sortConfig.direction === "ascending" ? "▲" : "▼") : ""}
                </Th>
              )
            ))}
          </Tr>
        </Thead>
        <tbody>
          {sortedData.map((row: any, index: number) => (
            <Tr key={index}>
              <Td>{indexed ? index + 1 : <Checkbox />}</Td>
              {Object.keys(columnsToDisplay).map((header, idx) => (
                filteredHeaders.includes(header) && (
                  <Td key={idx}>
                    {header === "lastMessageAt" ? formatDate(row[header]) : row[header]}
                  </Td>
                )
              ))}
            </Tr>
          ))}
        </tbody>
      </Table>
    </TableWrapper>
  );
};


const CustomDropdowns = ({ onSearch }: { onSearch: (search: string) => void }) => {
  const [search, setSearch] = useState("");
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const searchValue = e.target.value.trim();
    const columnName = "email";
    const operator = "==";
    
    // Format the search query as "columnName:==:searchValue"
    const formattedSearch = searchValue ? `${columnName}:${operator}:${searchValue}` : "";

    setSearch(searchValue);
    onSearch(formattedSearch); // Pass the formatted search query to the parent handler
  };
  const regionOptions = [
    { id: "all", text: "All" },
    { id: "region1", text: "Region 1" },
    { id: "region2", text: "Region 2" },
  ];

  const departmentOptions = [
    { id: "all", text: "All" },
    { id: "department1", text: "Department 1" },
    { id: "department2", text: "Department 2" },
  ];

  const classOptions = [
    { id: "all", text: "All" },
    { id: "class1", text: "Class 1" },
    { id: "class2", text: "Class 2" },
  ];

  const managerOptions = [
    { id: "all", text: "All" },
    { id: "manager1", text: "Manager 1" },
    { id: "manager2", text: "Manager 2" },
  ];

  return (
    <FiltersContainer>
      <Select label="Region" value="all" width="100%" items={regionOptions} />
      <Select label="Department" value="all" width="100%" items={departmentOptions} />
      <Select label="Class" value="all" width="100%" items={classOptions} />
      <Select label="Manager" value="all" width="100%" items={managerOptions} />
      <SearchContainer>
      <SearchInput
          type="text"
          placeholder="Search"
          value={search}
          onChange={handleSearchChange}
        />
        <AiOutlineSearch style={{ marginRight: "10px", fontSize: "20px", color: "#888" }} />
      </SearchContainer>
    </FiltersContainer>
  );
};

const DashboardComponent = () => {
  const { state, dispatch } = useStateContext();
  const [activeTab, setActiveTab] = useState("Details");
  const [data, setData] = useState<UserActivityInfo[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [searchText, setSearchText] = useState("");
  const [isFetching, setIsFetching] = useState(false); // State to manage loading state
  const containerRef = useRef<HTMLDivElement>(null);
  const rowsPerPage = 10;

  const fetchUserActivity = async (cursor: string | null, search: string) => {
    const filters = cursor
      ? `limit=${rowsPerPage}&cursor=${cursor}&order_by=createdAt:desc`
      : `limit=${rowsPerPage}&order_by=createdAt:desc`;

    const filtersWithSearch = search ? `${filters}&filters=${search}` : filters;
    console.log("filters", filtersWithSearch);
    const response = await getUserActivity(filtersWithSearch);
    return response;
  };

  // Query for initial and subsequent data loads
  const { isLoading, isError } = useQuery<ApiResponse<UserActivityInfo[] | undefined>>(
    ["userActivity", nextCursor, searchText],
    () => fetchUserActivity(nextCursor, searchText),
    {
      onSuccess: (fetchedData) => {
        setData((prevData) => [...prevData, ...(fetchedData?.data || [])]);
        setNextCursor(fetchedData?.data?.[fetchedData?.data?.length - 1]?.id || null);
        setIsFetching(false);
      },
      onError: () => {
        setIsFetching(false);
      },
      staleTime: 3000*60*1000,
      keepPreviousData: true,
    }
  );
  const aggregateData: any = useQueries([
    {
        queryFn: () => getNewChats(),
        queryKey: ["newChats"],
        staleTime: 10 * (60 * 1000)
    },
    {
        queryFn: () => getNewMsgs(),
        queryKey: ["newMessages"],
        staleTime: 10 * (60 * 1000)
    },
    {
        queryFn: () => getNewUploads(),
        queryKey: ["newUploads"],
        staleTime: 10 * (60 * 1000)
    },
    {
        queryFn: () => getNewKbs(),
        queryKey: ["newKbs"],
        staleTime: 10 * (60 * 1000)
    },
    {
      queryFn: () => getResumedChats(),
      queryKey: ["newResumedChats"],
      staleTime: 10 * (60 * 1000)
    }
  ])
  let newChats: number = 0; 
  let newMessages: number = 0;
  let newUploads: number = 0;
  let newKbs: number = 0; 
  let newResumedChats: number = 0;

  if(aggregateData && aggregateData.length === 5){
    newChats = aggregateData[0].data ? aggregateData[0].data.data : 0;
    newMessages = aggregateData[1].data ? aggregateData[1].data.data : 0;
    newUploads = aggregateData[2].data ? aggregateData[2].data.data : 0;
    newKbs = aggregateData[3].data ? aggregateData[3].data.data : 0;
    newResumedChats = aggregateData[4].data ? aggregateData[4].data.data : 0;
    // console.log("newChats: ", newChats)
    // console.log("newMessages: ", newMessages)
    // console.log("newUploads: ", newUploads)
    // console.log("newKbs: ", newKbs)
    // console.log("newResumedChats: ", newResumedChats)
  }

  // Handle scrolling to load more data
  const handleScroll = () => {
    if (containerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
      if (scrollHeight - scrollTop <= clientHeight + 50 && !isFetching && nextCursor) {
        loadMoreData();
      }
    }
  };

  const loadMoreData = () => {
    if (nextCursor) {
      setIsFetching(true);
    }
  };

  useEffect(() => {
    setData([]);
    setNextCursor(null);
    setIsFetching(true);
  }, [searchText]);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.addEventListener("scroll", handleScroll);
    }
    return () => {
      if (containerRef.current) {
        containerRef.current.removeEventListener("scroll", handleScroll);
      }
    };
  }, [handleScroll]);

  // Display loading or error messages
  if (isLoading && nextCursor === null) return <div>Loading...</div>;
  if (isError) return <div>Error fetching data</div>;

  const headers = data.length > 0 ? Object.keys(data[0]) : [];

  return (
    <div>
      {state.dashboardActiveTab === "UserSettings" && (
        <>
          {/* <CustomDropdowns onSearch={setSearchText}/> */}
          <ActivityDetailsContainer ref={containerRef}>
            <TableComponent indexed={false} headers={headers} data={data || []} />
          </ActivityDetailsContainer>
          <ButtonContainer>
            <ClassManagementButton backgroundColor="#ffffff" hoverColor="#084f8d" color="black">
              Edit
            </ClassManagementButton>
            <ClassManagementButton
              backgroundColor="#0a67b3"
              hoverColor="#084f8d"
              onClick={() => {
                dispatch({ type: "CLASS_MANAGEMENT_SETTINGS", payload: { isRightPanelOpen: true } });
              }}
            >
              Class Management
            </ClassManagementButton>
          </ButtonContainer>
        </>
      )}

      {state.dashboardActiveTab === "UserActivityDashboard" && (
        <ActivityDetailsContainer>
          {/* <CustomDropdowns onSearch={setSearchText}/> */}
          <DashboardContainer>
            <div className="d-flex flex-row align-items-start justify-content-start gap-4">
              <Reg_24>User Activity</Reg_24>
              <Select label="Date Range" value="year-to-date" width="50%" items={[{ id: "year-to-date", text: "Year to Date" }]} />
              {/* <RangeIndicator /> */}
            </div>
            <div className="d-flex flex-row align-items-center justify-content-between">
              <Widget value={newChats} label="New Chats" isNegative={true} percentageChange={-2.5} />
              <Widget value={newMessages} label="New Messages" isNegative={true} percentageChange={-2.5} />
              <Widget value={newResumedChats} label="Resumed Chats" isNegative={false} percentageChange={2.5} />
              <Widget value={newUploads} label="Documents Uploaded" isNegative={false} percentageChange={2.5} />
              <Widget value={newKbs} label="New Knowledge Bases" isNegative={true} percentageChange={-2.5} />
            </div>
          </DashboardContainer>
          <div className="d-flex flex-row align-items-start justify-content-start gap-4">
            <ActivityContainer>
              <div className="d-flex flex-row align-items-center justify-content-center gap-2 tabs">
                {/* <button className={`tab-link ${activeTab === "Overview" ? "active" : ""}`} onClick={() => setActiveTab("Overview")}>
                  Overview
                </button> */}
                <button className={`tab-link ${activeTab === "Details" ? "active" : ""}`} onClick={() => setActiveTab("Details")}>
                  Details
                </button>
              </div>
              {activeTab === "Overview" && <LineChartComponent />}
              {activeTab === "Details" && <TableComponent indexed={false} headers={headers} data={data || []} />}
            </ActivityContainer>
            {/* <SideContainer>
              <Reg_16 style={{ justifyContent: "center" }}>Most Billable Users</Reg_16>
              <TableComponent indexed={true} headers={["User's Email", "Billable Chart($)"]} data={BillableUsersData} />
              <DocumentFileSizeChart />
            </SideContainer> */}
          </div>
        </ActivityDetailsContainer>
      )}
    </div>
  );
};

export default DashboardComponent;
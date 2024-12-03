import { ReactComponent as Header } from "../../assets/icons/header.svg";
import { ReactComponent as AI } from "../../assets/icons/ai-logo.svg";
import { ReactComponent as Settings } from "../../assets/icons/brain.svg";
import { ReactComponent as PalmIcon } from "../../assets/icons/palm-icon.svg";
import { useStateContext } from "../../StateContext";
import styled from "styled-components";
import ProfileInitialsComponent from "./ProfileInitialsComponent"
import Dropdown from "../ui/DropdownHeaderComponent";
import "../../App.css";
import { useNavigate } from "react-router-dom";
import { UserInfo } from "../../api/model";

import { useState } from "react";
import DashboardComponent from "../functional/DashBoardComponent";
import BodyComponent from "./BodyComponent";
import { Button } from "../styling/components";
import { Reg_14 } from "../styling/typography";
import { ReactComponent as RightArrowIcon } from '../../assets/icons/right-arrow.svg';
import { minifyMessageLength } from "../../utils/helpers";
import Modal from "../functional/ModalComponent";
import { useMutation, useQueryClient } from "react-query";
import { deleteChat, markAsFavorite, updateChat } from "../../api/api";
import { InputTextBox } from "../ui/InputTextBox";
import { toast } from "react-toastify";

const NavOption = styled.li<{ active?: boolean }>`
    padding: 5px;
    cursor: pointer;
    border-bottom: ${(props) => props.active ? '2px solid var(--pill-hover)': ''}
`;

const HeaderComponent = ({
  user,
}: {
  user: UserInfo;
}) => {
  const { state, dispatch } = useStateContext();
  const navigate = useNavigate()
  const [dashBoardHeaders, setDashBoardHeaders] = useState(false);
  const [isFavModalVisible, setIsFavModalVisible] = useState(false);
  const [isRenameModalVisible, setIsRenameModalVisible] = useState(false);
  const [isDeleteModalVisible, setIsDeleteModalVisible] = useState(false);
  const [modalDialogText, setModalDialogText] = useState("");
  const [activeTab, setActiveTab] = useState("UserActivityDashboard");
  const [renameField, setRenameField] = useState("");
  const [isChatFavorite, setIsChatFavorte] = useState(state.chat?.favorite || false)
  const queryClient = useQueryClient()

  const { mutateAsync: markAsFavoriteMutation} = useMutation({
    mutationFn: async (chatId: string) => {
        const response = await markAsFavorite(chatId)
        if(response.success) {
          queryClient.invalidateQueries(["favorites"])
          queryClient.invalidateQueries(["todays"])
          queryClient.invalidateQueries(["sevenDaysAgo"])
          queryClient.invalidateQueries(["thirtyDaysAgo"])
          setIsChatFavorte(response.data || false)
        }
    }
  })

  const { mutateAsync: updateChatMutation} = useMutation({
    mutationFn: async (name: string) => {
        const response = await updateChat(state.chat?.id || "", name, [])
        if(response.success) {
          dispatch({type: 'RENAME_CHAT', payload: name})
          queryClient.invalidateQueries(["favorites"])
          queryClient.invalidateQueries(["todays"])
          queryClient.invalidateQueries(["sevenDaysAgo"])
          queryClient.invalidateQueries(["thirtyDaysAgo"])
          setIsRenameModalVisible(!isRenameModalVisible);
        }
    }
  })

  const { mutateAsync: deleteChatMutation} = useMutation({
    mutationFn: async () => {
        const response = await deleteChat(state.chat?.id || "")
        if(response.success) {
          queryClient.invalidateQueries(["favorites"])
          queryClient.invalidateQueries(["todays"])
          queryClient.invalidateQueries(["sevenDaysAgo"])
          queryClient.invalidateQueries(["thirtyDaysAgo"])
          dispatch({type: 'NEW_CHAT', payload: {}})
          navigate("/")
        }
    }
  })
  const handleTabClick = (tabName: string) => {
    setActiveTab(tabName);
    dispatch({
      type: "DASHBOARD_TAB",
      payload: {tab: tabName},
    });
  }

  const handleRename = async () => {
    setIsRenameModalVisible(!isRenameModalVisible)
    setRenameField(state.chatName || '')
  };

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href);
    toast.success("Chat link copied to clipboard");
  };

  const handleDelete = () => {
    setIsDeleteModalVisible(!isDeleteModalVisible)
    setModalDialogText(`Are you sure you want to delete: '${state.chatName}'?`)
  };
  
  const handleFavorite = () => {
    setIsFavModalVisible(!isFavModalVisible)
    setModalDialogText(isChatFavorite ? "Are you sure you want to remove this chat from favorite?" :"Are you sure you want to mark this chat as favorite?")
  };

  const toggleDashboardHeaders = () => {
    setDashBoardHeaders(!dashBoardHeaders);
    dispatch({
      type: "TOGGLE_DASHBOARD",
      payload: { isDashBoardOpen: !dashBoardHeaders },
    });
  };

  return (
    <>
      <Modal
        headerText={"Favorite Chat"}
        isVisible={isFavModalVisible}
        toggleModal={() => setIsFavModalVisible(!isFavModalVisible)}
        onSubmit={ () => {
          markAsFavoriteMutation(state.chat?.id || '')
          setIsFavModalVisible(!isFavModalVisible);
        }}
      >
        <>{modalDialogText}</>
      </Modal>
      <Modal
        headerText={"Rename Chat"}
        isVisible={isRenameModalVisible}
        toggleModal={() => setIsRenameModalVisible(!isRenameModalVisible)}
        onSubmit={ () => {
          updateChatMutation(renameField)
        }}
      >
        <InputTextBox value={renameField} label='Chat Name' width='100%' onChange={(x) => {setRenameField(x)}}></InputTextBox>
      </Modal>
      <Modal
        headerText={"Delete Chat"}
        isVisible={isDeleteModalVisible}
        toggleModal={() => setIsDeleteModalVisible(!isDeleteModalVisible)}
        onSubmit={ () => {
          deleteChatMutation()
          setIsDeleteModalVisible(!isDeleteModalVisible);
        }}
      >
        <>{modalDialogText}</>
      </Modal>
      <header className="header">
        <div className="logo" onClick={()=>{
            dispatch({type: 'NEW_CHAT', payload: {}})
            navigate("/")
          }}>
          <Header />
          <span>
            Scout{" "}
            <span className="superscript">
              <AI />
            </span>
          </span>
        </div>
        {!dashBoardHeaders ? (
          <div className="menu">
            {!state.isNewChat ? (
              <Dropdown
                details={minifyMessageLength(state.chatName || '', 20) || 'Loading...'}
                handleRename={handleRename}
                handleShare={handleShare}
                handleFavorite={handleFavorite}
                handleDelete={handleDelete}
                showDropdown={true}
              />
            ) : (
              <Dropdown
                details="New Chat"
                handleRename={handleRename}
                handleShare={handleShare}
                handleFavorite={handleFavorite}
                showDropdown={false}
              />
            )}
          </div>
        ) : (
          <div className="tabs">
            {/* <button
              className={`tab-link ${
                activeTab === "UserSettings" ? "active" : ""
              }`}
              onClick={() => handleTabClick("UserSettings")}
            >
              User Settings
            </button> */}
            <button
              className={`tab-link ${
                activeTab === "UserActivityDashboard" ? "active" : ""
              }`}
              onClick={() => handleTabClick("UserActivityDashboard")}
            >
              User Activity Dashboard
            </button>
          </div>
        )}
        <nav>
          <ul className="nav-list">
            {!dashBoardHeaders ? 
              <>
                <NavOption 
                  active={state.isRightPanelOpen && state.rightPanel === 'dashboard'}
                  onClick={() => {
                    dispatch({type: 'TOGGLE_USER_SETTINGS', payload: {}})
                  }}
                >
                  <PalmIcon onClick={toggleDashboardHeaders} />
                </NavOption>
                {/* <NavOption active={state.isRightPanelOpen && state.rightPanel === 'notifications'}>
                  <Notifications />
                </NavOption> */}
                <NavOption 
                  active={state.isRightPanelOpen && state.rightPanel === 'knowledge_base'}
                  onClick={() => {
                    dispatch({type: 'OPEN_KB', payload: {}})
                  }}>
                  <Settings />
                </NavOption>
                <NavOption active={state.isRightPanelOpen && (state.rightPanel === 'profile' || state.rightPanel === 'settings')}>
                  <ProfileInitialsComponent
                    firstName={user.firstName || ""}
                    lastName={user.lastName || ""}
                  />
                </NavOption>
              </> : 
              <div className="d-flex align-items-center justify-content-between gap-4">
                <NavOption 
                  active={state.isRightPanelOpen && state.rightPanel === 'dashboard'}
                  onClick={() => {
                    dispatch({type: 'TOGGLE_USER_SETTINGS', payload: {}})
                  }}
                >
                  <PalmIcon onClick={() => {}} />
                </NavOption>
                <Button onClick={toggleDashboardHeaders} style={{backgroundColor: '#FFD300', color: '#000', borderRadius: '30px', padding: '10px 10px'}}>
                    <Reg_14 style={{'justifyContent': 'space-between'}}>
                        Back to chat
                        <RightArrowIcon />
                    </Reg_14>
                </Button>
              </div>
            }
          </ul>
        </nav>
      </header>
      {dashBoardHeaders && (
        <BodyComponent>
          <div
            id="UserActivityDashboard"
            className={`tab-content ${
              activeTab === "UserActivityDashboard" ? "active" : ""
            }`}
          >
            <DashboardComponent />
          </div>
        </BodyComponent>
      )}
    </>
  );
};

export default HeaderComponent;

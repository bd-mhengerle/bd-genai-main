
import styled from "styled-components";
import { ReactComponent as OptionIcon } from "../../assets/icons/option-back.svg";
import { ReactComponent as PlusIcon } from "../../assets/icons/plus-icon.svg";
import { useState } from "react";
import { useStateContext } from "../../StateContext";
import { Switch } from "@mui/material";
import { Reg_11, Reg_12, Reg_14 } from "../styling/typography";
import { Select } from "../ui/Select";
import { Button } from "../styling/components";
import Modal from "./ModalComponent";

const Pill = styled.p`
    display: grid;
    border-radius: 50px;
    border-width: 2px;
    border-color: white;
    border-style: solid;
    align-items: center;
    padding: 5px 5px;
    margin: 10px 0;
`;

const Container = styled.div<{ isOpen?: boolean }>`
  display: flex;
  flex-direction: column;
  width: 303px;
  height: 100%;
  overflow-y: auto; /* Prevents scroll on the entire container */
  display: ${(props) => (props.isOpen ? "block" : "none")};
`;

const TextBox = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: start;
  align-items: start;
  padding: 10px 15px;
  margin: 10px;
  width: 95%;
  border-radius: 10px;
  border: 1px solid #ccc;
  background-color: #fff;
  font-family: Arial, sans-serif;
  font-size: 14px;
  color: #333;
`;

const MessageArea = styled.textarea`
  color: #555;
  width: 100%;
  font-size: 15px;
  outline: none;
  border: none;
  resize: none;
  rows: 6;
`;

const BottomContainer = styled.div`
  display: flex;
  flex-direction: column;
  width: 303px;
  height: 100%;
  overflow: hidden;
  margin-top:150%;
`;

const Title = styled.div`
  font-family: var(--bd-font-family);
  font-size: 18px;
  font-weight: 500;
  line-height: 21.94px;
  letter-spacing: -0.02em;
  text-align: left;
  color: var(--regular-font-color);
  height: 60px;
  width: 100%;
  cursor: pointer;
  & span {
    padding: 0 10px;
  }
`;

const Option = styled.div`
  font-family: var(--bd-font-family);
  font-size: 14px;
  font-weight: 500;
  line-height: 17.07px;
  letter-spacing: -0.02em;
  text-align: left;
  height: 50px;
  width: 100%;
  color: var(--regular-font-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  &:hover {
    background-color: var(--background-hover);
  }
`;

const Divider = styled.div`
  width: 100%;
  height: 1px;
  background-color: var(--divider);
`;

const SettingsComponent = () => {
  const { state, dispatch } = useStateContext();
  const [isSearchVisible, setIsSearchVisible] = useState(true);
  // const [isModalVisible, setIsModalVisible] = useState(false);
  // const [details, setDetails] = useState("");
  // const toggleModal = () => {
  //   setIsModalVisible(!isModalVisible);
  // };
  
  // const handleDetailsChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
  //   setDetails(e.target.value);
  // };

  const classOptions = [
    {text: 'Standard', id: 'standard'},
    {text: 'Premium', id: 'premium'}
  ];
  const tokenOptions = [
    {text: '1M', id: '1M'},
    {text: '10M', id: '10M'},
    {text: '100M', id: '100M'}
  ];
  const fileUploadOptions = [
    {text: '100Mb', id: '100Mb'},
    {text: '1Gb', id: '1Gb'},
    {text: '10Gb', id: '10Gb'}
  ];

  // const handleSubmit = () => {
  //   toggleModal();
  // };

  return (
    <Container isOpen={state.isRightPanelOpen}>
      {state.settings === "chat_settings" ? (
        <div id="settings">
          <div className="d-flex flex-column align-items-center justify-content-between p-2 mb-2">
            <Title
              onClick={() => {
                dispatch({ type: "OPEN_PROFILE", payload: {} });
              }}
            >
              <OptionIcon style={{ color: "var(--icon-color)" }} />
              <span>Chat Settings</span>
            </Title>
            <></>
            <Divider />
            <Option>
              <span>Dark Mode</span>
              <Switch
                checked={state.themeMode === "dark"}
                onChange={() => {
                  localStorage.setItem("theme-mode", state.themeMode === 'light' ? 'dark' : 'light');
                  dispatch({ type: "TOGGLE_THEME_MODE", payload: {} });
                }}
                inputProps={{ "aria-label": "Dark Mode" }}
              />
            </Option>
          </div>
        </div>
      ) : null}
      {state.settings === "account_settings" ? (
        <div id="account">
          <div className="d-flex flex-column align-items-center justify-content-between p-2 mb-2">
            <Title
              onClick={() => {
                dispatch({ type: "OPEN_PROFILE", payload: {} });
              }}
            >
              <OptionIcon style={{ color: "var(--icon-color)" }} />
              <span>Account Settings</span>
            </Title>
            <></>
            <Divider />
            <Option>
              <span>File Upload Limit</span>
              <span>100Mb per chat</span>  
            </Option>
            {/* <Option>
              <Button className="d-flex flex-row align-items-center justify-content-between" onClick={toggleModal}>
                <Reg_14 style={{'justifyContent': 'center'}}>
                    Request Increase
                </Reg_14>
                <Pill><PlusIcon  style={{height: '10px'}}/></Pill>
              </Button> 
            </Option> */}
          </div>
          {/* {isModalVisible &&
          <Modal
            headerText={"Limit Increase Request"}
            isVisible={isModalVisible}
            toggleModal={toggleModal}
            onSubmit={handleSubmit}
          >
            <TextBox>
              <MessageArea
                value={details}
                onChange={handleDetailsChange}
              />
            </TextBox>
          </Modal>} */}
        </div>
      ) : null}
      {state.settings === "terms_conditions" ? (
        <div id="terms">
        <div className="d-flex flex-column align-items-center justify-content-between p-2 mb-">
            <Title
            onClick={() => {
                dispatch({ type: "OPEN_PROFILE", payload: {} });
            }}
            >
            <OptionIcon style={{ color: "var(--icon-color)" }} />
            <span>Terms & Conditions</span>
            </Title>
            <></>
            <div>
            <span>
                <u>Your content</u> remains yours, which means that you retain
                any intellectual property rights that you have in your content.
                For example, you have <u>intellectual property rights</u> in the
                creative content you make, such as reviews you write. Or you may
                have the right to share someone else’s creative content if
                they’ve given you their permission. We need your permission if
                your intellectual property rights restrict our use of your
                content. You provide Google with that permission through this
                license.
            </span>
            <h4 className="mt-2">What’s covered</h4>
            <span>
                This license covers <u>your content</u> if that content is protected by
                intellectual property rights.
            </span>
            <h4 className="mt-2">What’s not covered</h4>
            <span>
                <ul>
                <li>
                    This license doesn’t affect your privacy rights — it’s only
                    about your intellectual property rights
                </li>
                <li>
                    This license doesn’t cover these types of content:
                    <ul>
                    <li>
                        publicly-available factual information that you provide,
                        such as corrections to the address of a local business.
                        That information doesn’t require a license because it’s
                        considered common knowledge that everyone’s free to use.
                    </li>
                    <li>
                        feedback that you offer, such as suggestions to improve
                        our services. Feedback is covered in the Service-related
                        communications section below.
                    </li>
                    </ul>
                </li>
                </ul>
            </span>
            <h4>Scope</h4>
            <span>
                <p>This license is:</p>
                <ul>
                <li>
                    worldwide, which means it’s valid anywhere in the world
                </li>
                <li>
                    non-exclusive, which means you can license your content to
                    others
                </li>
                <li>
                    royalty-free, which means there are no monetary fees for
                    this license
                </li>
                </ul>
            </span>
            </div>
        </div>
        </div>
        ) : null}
      {state.settings === "user_lockout" ? (
        <div id="user_lockout">
          <div className="d-flex flex-column align-items-center justify-content-between p-2 mb-2">
            <Title
              onClick={() => {
                dispatch({ type: "OPEN_USER_SETTINGS", payload: {} });
              }}
            >
              <OptionIcon style={{ color: "var(--icon-color)" }} />
              <span>User Lockout</span>
            </Title>
            <div>
              <Reg_11 className="mt-2"><b>Reason</b></Reg_11>
              <Reg_12>
                This is my reason why I need a limit increase. A scroll bar will appear if the user types more than the input box can hold. The Admin screen will get a notification. clicking on the notification link will show the user’s information with a dropdown showing their current ‘Class’. The Admin can either change the Class and Approve or Reject the request.
              </Reg_12>
              <Reg_11 className="mt-2"><b>User</b></Reg_11>
              <Reg_12>
                First Name
              </Reg_12>
              <Reg_11 className="mt-2"><b>Chats</b></Reg_11>
              <Reg_12>371</Reg_12>
              <Reg_11 className="mt-2"><b>Uploads</b></Reg_11>
              <Reg_12>298Mb</Reg_12>
              <Reg_11 className="mt-2"><b>BC Fees</b></Reg_11>
              <Reg_12>$276.18</Reg_12>
              <Reg_11 className="mt-4"></Reg_11>
              <Select label='Class' value='standard' width='100%' items={classOptions}></Select>
            </div>
            <></>
            <BottomContainer>
              <Divider/>
              <Button style={{background: '#00355A'}}>
                <Reg_14 style={{'justifyContent': 'center'}}>
                    Unlock User
                </Reg_14>
              </Button>
              <Button style={{background: '#E50000'}}>
                <Reg_14 style={{'justifyContent': 'center'}}>
                    Keep Locked Out
                </Reg_14>
              </Button>
            </BottomContainer>
          </div>
        </div>
      ) : null}
      {state.settings === "edit_class" ? (
        <div id="edit_class">
          <div className="d-flex flex-column align-items-center justify-content-between p-2 mb-2">
            <Title
              onClick={() => {
                dispatch({ type: "OPEN_CLASS_SETTING", payload: {} });
              }}
            >
              <OptionIcon style={{ color: "var(--icon-color)" }} />
              <span>Edit Class</span>
            </Title>
            <div className="d-flex flex-column align-items-start justify-content-between gap-2 w-100">
              <Select label='Class Name' value='standard' width='100%' items={classOptions}></Select>
              <Select label='Token Limits' value='1M' width='100%' items={tokenOptions}></Select>
              <Select label='File Upload Limits' value='100Mb' width='100%' items={fileUploadOptions}></Select>
              <Reg_11 className="mt-2"><b>User Count</b></Reg_11>
              <Reg_14>294</Reg_14>
            </div>
            <></>
            <BottomContainer>
              <Divider/>
              <Button style={{background: '#00355A'}}>
                <Reg_14 style={{'justifyContent': 'center'}}>
                    Update
                </Reg_14>
              </Button>
              <Button style={{background: '#FFFFFF'}}>
                <Reg_14 style={{'justifyContent': 'center'}}>
                    Cancel
                </Reg_14>
              </Button>
            </BottomContainer>
          </div>
        </div>
      ) : null}
      {state.settings === "new_class" ? (
        <div id="edit_class">
          <div className="d-flex flex-column align-items-center justify-content-between p-2 mb-2">
            <Title
              onClick={() => {
                dispatch({ type: "OPEN_CLASS_SETTING", payload: {} });
              }}
            >
              <OptionIcon style={{ color: "var(--icon-color)" }} />
              <span>Create Class</span>
            </Title>
            <div className="d-flex flex-column align-items-start justify-content-between gap-2 w-100">
              <Select label='Class Name' value='' width='100%' items={classOptions}></Select>
              <Select label='Token Limits' value='' width='100%' items={tokenOptions}></Select>
              <Select label='File Upload Limits' value='' width='100%' items={fileUploadOptions}></Select>
            </div>
            <></>
            <BottomContainer>
              <Divider/>
              <Button style={{background: '#00355A'}}>
                <Reg_14 style={{'justifyContent': 'center'}}>
                    Create
                </Reg_14>
              </Button>
              <Button style={{background: '#FFFFFF', color: '#00355A'}}>
                <Reg_14 style={{'justifyContent': 'center'}}>
                    Cancel
                </Reg_14>
              </Button>
            </BottomContainer>
          </div>
        </div>
      ) : null}
    </Container>

  );
};

export default SettingsComponent;

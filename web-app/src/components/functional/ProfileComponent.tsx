import styled from 'styled-components';
import { ReactComponent as LogoutIcon } from '../../assets/icons/logout-icon.svg';
import { ReactComponent as OptionIcon } from '../../assets/icons/option-next.svg';
import { useStateContext } from '../../StateContext';
import { Reg_18 } from "../styling/typography"
import { useNavigate } from 'react-router-dom';
import Modal from "../functional/ModalComponent";
import { useState } from 'react';

const Container = styled.div<{ isOpen?: boolean }>`
    display: flex;
    flex-direction: column;
    width: 303px;
    height: 100%;
    overflow: hidden; /* Prevents scroll on the entire container */
    display: ${(props) => (props.isOpen ? 'block' : 'none')};
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
    display:flex;
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

const ProfileComponent = () => {
    const { state, dispatch } = useStateContext();
    const navigate = useNavigate()
    const [isModalOpen, setIsModalOpen] = useState(false)

      return (
        <Container isOpen={state.isRightPanelOpen}>
            <Modal
                headerText={"Log Out"}
                isVisible={isModalOpen}
                toggleModal={() => setIsModalOpen(!isModalOpen)}
                onSubmit={ () => {
                    window.location.href = `${window.location.origin}?gcp-iap-mode=CLEAR_LOGIN_COOKIE`
                }}
            >
                <>Do you want to log out?</>
            </Modal>
            <div id="configuration">
                <div className="d-flex flex-column align-items-center justify-content-between p-2 mb-2">
                  
                    <Reg_18>Profile</Reg_18>
                    <></>
                    <Option onClick={() => {
                        dispatch({type: 'PROFILE_SETTINGS', payload: {setting: 'chat_settings'}})
                    }}>
                        <span>Chat Settings</span>
                        <OptionIcon style={{color: 'var(--icon-color)'}}/>
                    </Option>
                    <Divider />
                    <Option onClick={() => {
                        dispatch({type: 'PROFILE_SETTINGS', payload: {setting: 'account_settings'}})
                    }}>
                        <span>Account Settings</span>
                        <OptionIcon style={{color: 'var(--icon-color)'}}/>
                    </Option>
                    <Divider />
                    <Option onClick={() => {
                        dispatch({type: 'PROFILE_SETTINGS', payload: {setting: 'terms_conditions'}})
                    }}>
                        <span>Terms and Conditions</span>
                        <OptionIcon style={{color: 'var(--icon-color)'}}/>
                    </Option>
                    <Divider />
                    <Option onClick={() => {
                        setIsModalOpen(true)
                    }}>
                        <span>Log Out</span>
                        <LogoutIcon style={{color: 'var(--icon-color)'}}/>
                    </Option>
                </div>
            </div>    
        </Container>
    );
}

export default ProfileComponent;

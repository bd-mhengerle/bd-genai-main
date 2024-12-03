import styled from 'styled-components';
import { ReactComponent as LogoutIcon } from '../../assets/icons/logout-icon.svg';
import { ReactComponent as OptionIcon } from '../../assets/icons/option-next.svg';
import { useStateContext } from '../../StateContext';
import { Reg_18 } from "../styling/typography"

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

const DashBoardSettingsComponent = () => {
    const { state, dispatch } = useStateContext();

      return (
        <Container isOpen={state.isRightPanelOpen}>
            <div id="configuration">
                <div className="d-flex flex-column align-items-center justify-content-between p-2 mb-2">
                  
                    <Reg_18>Current Tasks</Reg_18>
                    <></>
                    <Option onClick={() => {
                        dispatch({type: 'DASHBOARD_SETTINGS', payload: {setting: 'user_lockout'}})
                    }}>
                        <span>User Lockout</span>
                        <OptionIcon style={{color: 'var(--icon-color)'}}/>
                    </Option>
                    <Divider />
                    <Option onClick={() => {
                        dispatch({type: 'DASHBOARD_SETTINGS', payload: {setting: 'review_usage'}})
                    }}>
                        <span>Review Usage</span>
                        <OptionIcon style={{color: 'var(--icon-color)'}}/>
                    </Option>
                    <Divider />
                    <Option onClick={() => {
                        dispatch({type: 'DASHBOARD_SETTINGS', payload: {setting: 'support_question'}})
                    }}>
                        <span>Support Question</span>
                        <OptionIcon style={{color: 'var(--icon-color)'}}/>
                    </Option>
                </div>
            </div>    
        </Container>
    );
}

export default DashBoardSettingsComponent;

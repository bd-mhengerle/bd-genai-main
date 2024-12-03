import styled from 'styled-components';
import { ReactComponent as OptionIcon } from '../../assets/icons/option-next.svg';
import { useStateContext } from '../../StateContext';
import { Reg_11, Reg_12, Reg_14, Reg_18 } from "../styling/typography"
import { Button } from '../styling/components';

const Container = styled.div<{ isOpen?: boolean }>`
    display: flex;
    flex-direction: column;
    width: 303px;
    height: 100%;
    overflow: hidden; /* Prevents scroll on the entire container */
    display: ${(props) => (props.isOpen ? 'block' : 'none')};
`;

const BottomContainer = styled.div`
  display: flex;
  flex-direction: column;
  width: 303px;
  height: 100%;
  overflow: hidden;
  margin-top:140%
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

const ClassManagementSettingsComponent = () => {
    const { state, dispatch } = useStateContext();

      return (
        <Container isOpen={state.isRightPanelOpen}>
            <div id="configuration">
                <div className="d-flex flex-column align-items-center justify-content-between p-2 mb-2">
                  
                    <Reg_18>Class Management</Reg_18>
                    <></>
                    <Option onClick={() => {
                        dispatch({type: 'TOGGLE_CLASS_SETTING', payload: {setting: 'edit_class'}})
                    }}>
                        <div className='d-flex flex-column align-items-start justify-content-between'>
                            <span>Standard</span>
                            <Reg_12>1m Tokens - 100Mb per Chat - 294 users</Reg_12>
                        </div>
                        <OptionIcon style={{color: 'var(--icon-color)'}}/>
                    </Option>
                    <Divider />
                    <Option onClick={() => {
                        dispatch({type: 'TOGGLE_CLASS_SETTING', payload: {setting: 'edit_class'}})
                    }}>
                        <div className='d-flex flex-column align-items-start justify-content-between'>
                            <span>Power Uploader</span>
                            <Reg_12>1m Tokens - 1Gb per Chat - 7 users</Reg_12>
                        </div>
                        <OptionIcon style={{color: 'var(--icon-color)'}}/>
                    </Option>
                    <Divider />
                    <Option onClick={() => {
                        dispatch({type: 'TOGGLE_CLASS_SETTING', payload: {setting: 'edit_class'}})
                    }}>
                        <div className='d-flex flex-column align-items-start justify-content-between'>
                            <span>Power Token</span>
                            <Reg_12>10m Tokens - 100Mb per Chat - 12 users</Reg_12>
                        </div>
                        <OptionIcon style={{color: 'var(--icon-color)'}}/>
                    </Option>
                    <Divider />
                    <Option onClick={() => {
                        dispatch({type: 'TOGGLE_CLASS_SETTING', payload: {setting: 'edit_class'}})
                    }}>
                         <div className='d-flex flex-column align-items-start justify-content-between'>
                            <span>Unlimited</span>
                            <Reg_12>500m Tokens - 100Gb per Chat - 3 users</Reg_12>
                        </div>
                        <OptionIcon style={{color: 'var(--icon-color)'}}/>
                    </Option>
                    <Divider />
                </div>
                <BottomContainer>
                    <Divider/>
                    <Button 
                        style={{background: '#00355A'}}
                        onClick={() => {
                            dispatch({type: 'TOGGLE_CLASS_SETTING', payload: {setting: 'new_class'}})
                        }}
                    >
                        <Reg_14 style={{'justifyContent': 'center'}}>
                            + Add New Class
                        </Reg_14>
                    </Button>
                </BottomContainer>
            </div>    
        </Container>
    );
}

export default ClassManagementSettingsComponent;

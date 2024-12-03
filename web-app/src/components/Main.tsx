import styled from 'styled-components';
import HeaderComponent from './layout/HeaderComponent';
import BodyComponent from './layout/BodyComponent';
import SidePanelComponent from './layout/SidePanelComponent';
import HistoryComponent from './functional/HistoryComponent';
import { useStateContext } from '../StateContext';
import SettingsComponent from './functional/SettingsComponent';
import ProfileComponent from './functional/ProfileComponent';
import { ChatComponent } from "./functional/ChatComponent"
import { KnowledgeBaseContainer } from "./functional/KnowledgeBaseContainer"
import { useQuery } from 'react-query';
import { getUserInfo } from '../api/api';
import DashBoardSettingsComponent from './functional/DashboardSettingsComponent';
import ClassManagementSettingsComponent from './functional/ClassManagementSettings';
import { UserInfo } from '../api/model';


const Wrapper = styled.div`
  height: 100vh;
  width: 100vw;
  display: grid;
  grid-template-rows: 60px calc(100vh - 60px);
  grid-template-columns: 360px auto 360px;
  position: relative;
  background-color: var(--background);
  font-family: var(--bd-font-family);
  color: var(--font-color);
`;
export const MainComponent = () => {
    const { state, dispatch } = useStateContext();
    const { isLoading } = useQuery({
        queryFn: async () => {
            if(!state.user.email){
                const us = await getUserInfo()
                
                dispatch({type: 'SET_USER', payload: getUser(us.data)})
                return us.data
            }
            return state.user
        },
        queryKey: ["userInfo"]
    })
    const getUser = (user: UserInfo | undefined): UserInfo => {
        let res = {
            createdAt: '',
            email: '',
            id: '',
            updatedAt: '',
            firstName: '',
            lastName: ''
        }
        res = {...res, ...user}
        if(user && !user.firstName) {
            const email = user.email
            if(email) {
                const match = email.match(/^(\w+)\.(\w+)@/);
                if(match?.length == 3) {
                    res.firstName = match[1]
                    res.lastName = match[2]
                } else {
                    res.firstName = email.substring(0,1)
                }
            }
        }
        return res
    }

    return (
        <>
            <Wrapper className={`insights-${state.themeMode}`}>
                <HeaderComponent user={state.user}></HeaderComponent>
                <SidePanelComponent position='left'><HistoryComponent></HistoryComponent></SidePanelComponent>
                {
                    state.isDashBoardOpen ? 
                    <>                   
                    </> : 
                    <BodyComponent>
                        <ChatComponent></ChatComponent>
                    </BodyComponent>
                }
                <SidePanelComponent position='right'>
                    {state.rightPanel === 'profile' && <ProfileComponent></ProfileComponent>}
                    {state.rightPanel === 'settings' && <SettingsComponent></SettingsComponent>}
                    {state.rightPanel === 'knowledge_base' && <KnowledgeBaseContainer></KnowledgeBaseContainer>}
                    {state.rightPanel === 'dashboard' && <DashBoardSettingsComponent></DashBoardSettingsComponent>}
                    {state.rightPanel === 'class_management' && <ClassManagementSettingsComponent></ClassManagementSettingsComponent>}
                </SidePanelComponent>
            </Wrapper>
        </>
    );
};
import styled from 'styled-components';
import { ReactComponent as SearchIcon } from '../../assets/icons/search-icon.svg';
import { ReactComponent as SendIcon } from '../../assets/icons/send-icon-horizontal.svg';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTimes } from '@fortawesome/free-solid-svg-icons';
import { useState } from 'react';
import { useStateContext } from '../../StateContext';
import { Reg_18, Reg_14 } from "../styling/typography"
import { Button } from "../styling/components"
import { useQueries, useQuery } from 'react-query';
import { getFavorites, getTodays, getSevenDaysAgo, getThirtyDaysAgo } from "../../api/api"
import { PillComponent } from './PillComponent';
import { useNavigate } from 'react-router-dom';
import { ChatModel } from '../../api/model';
import { minifyMessageLength } from '../../utils/helpers';

const Container = styled.div<{ isOpen?: boolean }>`
    display: flex;
    flex-direction: column;
    width: 303px;
    height: 100%;
    overflow: hidden; /* Prevents scroll on the entire container */
    display: ${(props) => (props.isOpen ? 'block' : 'none')};
`;

const ScrollableContent = styled.div`
    flex: 1; /* Takes up remaining space within the Container */
    overflow-y: auto; /* Enables vertical scrolling */
    padding-right: 10px; /* Ensures padding on the right side for the scrollbar */
    height: 70vh;
`;

const SearchWrapper = styled.div`
  display: flex;
  align-items: center;
  position: relative;
`;

const StyledSearchInput = styled.input`
    width: 100%;
    border: none;
    padding: 10px 40px 10px 35px;
`;

const IconWrapper = styled.div`
    position: absolute;
    left: 10px;
    top: 50%;
    transform: translateY(-50%);
    cursor: pointer;
`;

const CloseIcon = styled(FontAwesomeIcon)`
    position: absolute;
    top: 50%;
    right: 10px;
    transform: translateY(-50%);
    cursor: pointer;
    color: #aaa;
`;

const Option = styled.div`
    padding-top: 25px;
    padding-bottom: 15px;

`


const HistoryComponent = () => {
    const { state, dispatch } = useStateContext();
    const [isSearchVisible, setIsSearchVisible] = useState(true);
    const [searchText, setSearchText] = useState('')
    const navigate = useNavigate()
    const chats = useQueries([
        {
            queryFn: () => getFavorites(),
            queryKey: ["favorites"],
            staleTime: 10 * (60 * 1000)
        },
        {
            queryFn: () => getTodays(),
            queryKey: ["todays"],
            staleTime: 10 * (60 * 1000)
        },
        {
            queryFn: () => getSevenDaysAgo(),
            queryKey: ["sevenDaysAgo"],
            staleTime: 10 * (60 * 1000)
        },
        {
            queryFn: () => getThirtyDaysAgo(),
            queryKey: ["thirtyDaysAgo"],
            staleTime: 10 * (60 * 1000)
        }
    ])
    let favorites: ChatModel[] = [];
    let todays: ChatModel[] = [];
    let sevenDaysAgo: ChatModel[] = [];
    let thirtyDaysAgo: ChatModel[] = [];

    if(chats && chats.length === 4){
        favorites = chats[0].data ? chats[0].data?.data.filter((x: ChatModel) => {
            if(searchText){
                return x.name.toLowerCase().includes(searchText.toLowerCase())
            }
            return true;
        }) : []
        todays = chats[1].data ? chats[1].data?.data.filter((x: ChatModel) => {
            if(searchText){
                return x.name.toLowerCase().includes(searchText.toLowerCase())
            }
            return true;
        }) : []
        sevenDaysAgo = chats[2].data ? chats[2].data?.data.filter((x: ChatModel) => {
            if(searchText){
                return x.name.toLowerCase().includes(searchText.toLowerCase())
            }
            return true;
        }) : []
        thirtyDaysAgo = chats[3].data ? chats[3].data?.data.filter((x: ChatModel) => {
            if(searchText){
                return x.name.toLowerCase().includes(searchText.toLowerCase())
            }
            return true;
        }) : []
    }

    const toggleSearch = () => {
        setIsSearchVisible(!isSearchVisible);
    };

    const startChat = (id?: string) => {
        if(id) {
            dispatch({type: 'LOAD_CHAT', payload: {}})
            navigate(`/${id}`)
        } else {
            dispatch({type: 'NEW_CHAT', payload: {}})
            navigate("/")
        }
    };

    const handleClick = (index: number, history: number) => {
        
    };
    const handleDelete = (index: number, history: number) => {
    }

    const handleDeleteChatCall = async (chatId: string) => {
        try {
            const header = process.env.REACT_APP_API_TOKEN ? new Headers({
                'Authorization': 'Bearer '+process.env.REACT_APP_API_TOKEN, 
              }) : new Headers({})
            const response = await fetch(`${process.env.REACT_APP_API_BASE_URL}/chat/${chatId}`, {
                method: "DELETE",
                headers: header
            });
            const responseData = await response.json();
            console.log(responseData);
            if (responseData.deleted) {
                console.log("Chat deleted successfully");
            }
        } catch (error) {
            console.log(error);
        }
    }

    const handleRename = (index: number, editedText: string, history: number) => {
    }

    const handleRenameCall = async (id: string, rename: string) => {
        try {
            const header = process.env.REACT_APP_API_TOKEN ? new Headers({
                'Authorization': 'Bearer '+process.env.REACT_APP_API_TOKEN, 
                "Content-Type": "application/json",
              }) : new Headers({
                "Content-Type": "application/json",
              })
          const response = await fetch(`${process.env.REACT_APP_API_BASE_URL}/chat/${id}`, {
            method: "PUT",
            headers: header,
            body: JSON.stringify({ name: rename, tags: [] }),
          });
      
          const responseData = await response.json();
          return responseData;
    
        } catch (error) {
          console.log(error);
        }
      };

      return (
        <Container isOpen={state.isHistoryOpen}>
            <div id="history">
                <div className="d-flex align-items-center justify-content-between p-2">
                   {isSearchVisible ? 
                    <>
                        <Reg_18>History</Reg_18>
                        <SearchWrapper>
                            <SearchIcon onClick={toggleSearch} style={{ cursor: 'pointer' }} />
                        </SearchWrapper> 
                    </> : 
                    <>
                        <SearchWrapper className="w-100">
                            <StyledSearchInput 
                                type="text" 
                                placeholder="Search..." 
                                value={searchText} 
                                onChange={(e)=> {setSearchText(e.target.value)}}/>
                            <IconWrapper onClick={toggleSearch} style={{ cursor: 'pointer' }}>
                                <SearchIcon />
                            </IconWrapper>
                            <CloseIcon icon={faTimes} onClick={toggleSearch} />
                        </SearchWrapper> 
                    </>}
                </div>
                <Button onClick={()=> {startChat()}}>
                    <Reg_14 style={{'justifyContent': 'space-between'}}>
                        Start a new chat 
                        <SendIcon />
                    </Reg_14>
                </Button>
            </div>
            <ScrollableContent>
                <Option>
                    <Reg_14>Favorites</Reg_14>
                </Option> 
                {favorites.map(x => {
                    return <PillComponent 
                        name={minifyMessageLength(x.name, 50)} 
                        id={x.id} 
                        favorite={x.favorite}
                        handleDelete={() =>{}}
                        handleFavouriteToggle={() => {}}
                        handleClick={(id)=> {
                            startChat(id)
                        }}
                        handleRename={() => {}}></PillComponent>
                })}
                <Option>
                    <Reg_14>Today</Reg_14>
                </Option> 
                {todays.map(x => {
                    return <PillComponent 
                        name={minifyMessageLength(x.name, 50)} 
                        id={x.id} 
                        favorite={x.favorite}
                        handleDelete={() =>{}}
                        handleFavouriteToggle={() => {}}
                        handleClick={(id) => {
                            startChat(id)
                        }}
                        handleRename={() => {}}></PillComponent>
                })}
                <Option>
                    <Reg_14>Previous 7 Days</Reg_14>
                </Option> 
                {sevenDaysAgo.map(x => {
                    return <PillComponent 
                        name={minifyMessageLength(x.name, 50)} 
                        id={x.id} 
                        favorite={x.favorite}
                        handleDelete={() =>{}}
                        handleFavouriteToggle={() => {}}
                        handleClick={(id) => {
                            startChat(id)
                        }}
                        handleRename={() => {}}></PillComponent>
                })}
                <Option>
                    <Reg_14>Previous 30 Days</Reg_14>
                </Option> 
                {thirtyDaysAgo.map(x => {
                    return <PillComponent 
                        name={minifyMessageLength(x.name, 50)} 
                        id={x.id} 
                        favorite={x.favorite}
                        handleDelete={() =>{}}
                        handleFavouriteToggle={() => {}}
                        handleClick={(id) => {
                            startChat(id)
                        }}
                        handleRename={() => {}}></PillComponent>
                })}
            </ScrollableContent>       
        </Container>
    );
}

export default HistoryComponent;

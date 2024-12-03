import styled from 'styled-components';
import { ReactComponent as AiIcon } from '../../assets/icons/ai-chat.svg';
import { useStateContext } from '../../StateContext';
import { Reg_14, Reg_10 } from "../styling/typography"
import { Message } from '../../api/model';
import Markdown from 'react-markdown'
import { memo, useEffect, useRef } from 'react';
import CitationComponent from './CitationComponent';

const Wrapper = styled.div`
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    overflow:auto;
`;

const MessageWrapper = styled.div`
    width: 100%;
    display: flex;
    justify-content: center;
    flex-direction: row;

    &.user {
        justify-content: end;
    }

    &.agent {
        justify-content: start;
    }
`;

const UserBubble = styled.div`
    background-color: var(--chat-bubble-bg);
    color: var(--file-bubble-color);
    padding: 5px;
    marding: 10px 0;
    border-radius: 8px;
    margin: 10px 0;
    max-width: 90%;
`

const AgentBubble = styled.div`
    background-color: var(--background);
    opacity: 25;
    color: var(--file-bubble-color);
    padding: 5px;
    border-radius: 8px;
    margin: 10px 0;
    max-width: 90%;
`

const Initials = styled.div`
    width: 30px;
    height: 30px;
    background-color: var(--bg-color-initials);
    color: var(--font-color-initials);
    display: flex;
    justify-content: center;
    align-items: center;
    border-radius: 50%;
    margin: 10px;
    padding: 10px 0;
    text-transform: uppercase;
`

const CitationContainer = styled.div`
    display: flex;
    flex.direction: column;
    justify-content: start;
    flex-wrap: wrap;
`


export const ChatHistoryComponent = memo(() => {
    const { state } = useStateContext();
    const messagesEndRef = useRef<null | HTMLDivElement>(null)
    useEffect(() => {
        console.log("scrolling")
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }, [state.scrollPosition]);
    
    const getInitials = (firstName: string, lastName: string): string => {
        return `${firstName ? firstName[0]: ''}${lastName ? lastName[0] : ''}`;
    };
    return (
        <Wrapper>
            {state.history.map(x => {
                if(x.role === "user") {
                    return (
                    <MessageWrapper className='user'>
                        <UserBubble>{x.content}</UserBubble>
                        <Initials>
                            <Reg_14>{getInitials(state.user.firstName || '', state.user.lastName || '')}</Reg_14>
                        </Initials>
                    </MessageWrapper>)
                }
                else if(x.role === "assistant-loading"){
                    return (
                    <MessageWrapper className='agent'>
                        <AiIcon style={{margin: "10px"}}/>
                        <AgentBubble>
                            <div dangerouslySetInnerHTML={{__html: x.content}} />
                        </AgentBubble>
                    </MessageWrapper>)
                } else {
                    return (
                        <MessageWrapper className='agent'>
                            <AiIcon style={{margin: "10px"}}/>
                            <AgentBubble>
                                <Markdown>{x.content}</Markdown>
                                <CitationContainer>
                                {x.citations && x.citations.map(c => {
                                    return (
                                        <CitationComponent id={c.citation} />
                                    )
                                })}
                                </CitationContainer>
                            </AgentBubble>
                        </MessageWrapper>)
                }
            })}
            <div ref={messagesEndRef}></div>
        </Wrapper>
    );
});
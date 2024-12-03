import styled from 'styled-components';
import { ReactComponent as PlusIcon } from '../../assets/icons/plus-icon.svg';
import { ReactComponent as FileIcon } from "../../assets/icons/file-attachement.svg";
import { ReactComponent as SendIcon } from "../../assets/icons/send-icon.svg";
import { ReactComponent as MicIcon } from "../../assets/icons/mic-icon.svg";
import { ReactComponent as AttachmentIcon } from "../../assets/icons/attachment.svg";
import { ReactComponent as TrashIcon } from "../../assets/icons/trash.svg";
import { memo, useCallback, useRef, useState } from 'react';
import { useStateContext } from '../../StateContext';
import { PillComponent } from './PillComponent';
import { useMutation, useQuery, useQueryClient } from 'react-query';
import { addFilesToKb, askToBot, createChat, fetchChat } from '../../api/api';
import { useNavigate, useParams } from 'react-router-dom';
import { KnowledgeBaseModel, Message } from '../../api/model';
import { ChatHistoryComponent } from './ChatHistoryComponent';
import Modal from "../functional/ModalComponent";
import { toast } from 'react-toastify';
import { Reg_10, Reg_12 } from '../styling/typography';
import { useDropzone } from 'react-dropzone';

const Wrapper = styled.div`
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
`;

const Suggest = styled.div`
    width: 80%;
    height: auto;
    display: flex;
    justify-content: center;
    & > * {
        margin: 0 10px;
    }
`;

const ChatInputWrapper = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  border: 0.5px solid #00355a;
  border-radius: 12px;
  padding: 15px 20px;
  gap: 10px;
  width: 80%;
  margin: 15px 45px;
  background-color: var(--background);
`;

const StyledTextarea = styled.textarea`
    border: none;
    border-radius: 0;
    padding: 0.375rem 0.75rem;
    background-color: var(--background);
    color: var(--font-color);
    flex-grow: 1;
    resize: none;
    max-height: 60vh;
    overflow: auto;
    line-height: 1.5;
    font-size: 1rem;
    &:focus {
        outline: none;
        box-shadow: none;
    }
`;

const FilesArea = styled.div`
    width: 100%;
    display: flex;
    align-items: center;
    background-color: var(--background);
    color: var(--font-color);
    border-width: 1px;
    border-style: dashed;
    border-color: var(--file-area-border);
    border-radius: 8px;
    height: 50px;
    justify-content: center;
    margin: 10px 0;
`;

const File = styled.div`
    width: 100%;
    display: grid;
    grid-template-columns: 30px calc(100% - 60px) 30px;
    align-items: center;
    background-color: var(--file-bubble);
    color: var(--file-bubble-color);
    border: none;
    border-radius: 30px;
    height: 25px;
    justify-content: center;
    margin: 10px 0;
    cursor: pointer;
    position: relative;
`;

const Icon = styled.div`
    width: 100%;
    display:flex;
    justify-content: center;
`;


const defaultPrompts = [
    "What should I work on today?",
    "Summarize my unread emails today"
];

export const ChatComponent = memo(() => {
    const { state, dispatch } = useStateContext();
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const [isModalVisible, setIsModalVisible] = useState(false);
    const [message, setMessage] = useState("");
    const [myFiles, setMyFiles] = useState<File[]>([])
    const queryClient = useQueryClient()
    const { id } = useParams();
    const navigate = useNavigate()
    const onDrop = useCallback((acceptedFiles: File[]) => {
        setMyFiles([...myFiles, ...acceptedFiles])
    }, [myFiles])
    const {acceptedFiles, getRootProps, getInputProps} = useDropzone({
        onDrop
    });

    const { mutateAsync: addChatMutation} = useMutation({
        mutationFn: async (text: string) => {
            const response = await createChat(text)
            if(response.success) {
                dispatch({type: 'SET_CHAT_NAME', payload: {id: response.data, name: text}})
                navigate(`/${response.data}`)
            }
        },
        onSuccess: () => {
            queryClient.invalidateQueries(["todays"])
        }
    })

    const { mutateAsync: askBotMutation} = useMutation({
        mutationFn: async(question: {message: string, id: string}) => {
            const saved = localStorage.getItem("kbs");
            const currentKbs = saved? JSON.parse(saved || '') : [];
            const kbs = currentKbs && currentKbs.length ? currentKbs.filter((x: KnowledgeBaseModel) => x.active && x.id).map((x: KnowledgeBaseModel) => x.id) : []
            kbs.push(state.chat?.kbId)
            const response = await askToBot(question.id, question.message, kbs, state.model)
            let chatMessages: Message[] = state.history;
            if(response.success) {
                chatMessages = chatMessages.filter(x => x.role !== "assistant-loading")
                if(response.data){ 
                    chatMessages.push(response.data)
                }
                dispatch({type: 'SET_HISTORY', payload: chatMessages})
            } else {
                if(chatMessages.length === 0) {
                    chatMessages.push({role: "user", content: question.message, id: 'temporary'})
                }
                chatMessages = chatMessages.filter(x => x.role !== "assistant-loading")
                chatMessages.push({role: "assistant", content: `<span class='error'>${response.message}</span>`, id: 'temporary'})
                
                dispatch({type: 'SET_HISTORY', payload: chatMessages})
            }
        },
    })

    const { mutateAsync: addFilesMutation, isLoading: isSaving} = useMutation({
        mutationFn: async () => {
            if(acceptedFiles.length){
                const response = await addFilesToKb(state.chat?.kbId || '', myFiles)
                if(response.success) {
                    if(response.data?.embedding_results){
                        for (const [key, value] of Object.entries(response.data?.embedding_results)) {
                            if(value === 'success') {
                                toast.success(`File ${key} indexed succesfully`)
                            } else {
                                toast.error(`File ${key} couldn't be indexed`)
                            }
                        }
                    }
                    setMyFiles([])
                    toggleModal()
                }
            }
        },
    })

    useQuery({
        queryFn: async () => {
            if(id) {
                const response = await fetchChat(id || '')
                return response
            }
            return undefined
        },
        queryKey: ["chat_data",{id}],
        onSuccess: (data) => {
            if(data && data.success){
                let chatMessages: Message[] = data.data?.history || [];
                dispatch({type: 'SET_CHAT_NAME', payload: data.data})
                if(data.data?.history.length === 0 && state.history.length === 0) {
                    askBotMutation({message: data.data.name, id: data.data.id})
                    chatMessages.push({role: "user", content: data.data.name, id: 'temporary'})
                    chatMessages.push({role: "assistant-loading", content: "<span class='assistant-waiting'>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span>", id: 'temporary'})
                }
                dispatch({type: 'SET_HISTORY', payload: chatMessages})
            }
        }
    })

    const handleInput = (event: any) => {
        const textarea = event.target;
        textarea.style.height = "auto"; // Reset height
        textarea.style.height = `${textarea.scrollHeight}px`; // Set new height
        setMessage(textarea.value);
    };

    const handleKeyDown = (e: any) => {
        if (e.key === "Enter") {
            if (e.shiftKey) {
            // Allow newline with Shift+Enter
            return;
            } else {
            // Prevent default Enter behavior (new line) and send message
            e.preventDefault();
            sendMessage();
            }
        }
    };

    function formatBytes(bytes: number, decimals = 1) {
        if (!+bytes) return '0 Bytes'
    
        const k = 1024
        const dm = decimals < 0 ? 0 : decimals
        const sizes = ['b', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']
    
        const i = Math.floor(Math.log(bytes) / Math.log(k))
    
        return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`
    }

    const sendMessage = async () => {
        if (message.trim()) {
            if(!state.chat?.id) {
                try {
                    await addChatMutation(message)
                    setMessage("");
                    if (textareaRef.current) {
                        textareaRef.current.style.height = "auto";
                        textareaRef.current.rows = 1;
                    }
                }
                catch (e) {
    
                }
            }
            else {
                askBotMutation({message: message, id: state.chat?.id})
                let chatMessages: Message[] = state.history;
                chatMessages.push({role: "user", content: message, id: 'temporary'})
                chatMessages.push({role: "assistant-loading", content: "<span class='assistant-waiting'>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span>", id: 'temporary'})
                dispatch({type: 'SET_HISTORY', payload: chatMessages})
                setMessage("");
                if (textareaRef.current) {
                    textareaRef.current.style.height = "auto";
                    textareaRef.current.rows = 1;
                }
            }
        }
    };

    const toggleModal = () => {
        if(state.chat){
            setIsModalVisible(!isModalVisible);
        } else {
            toast.warning("You can only upload a file to an existing chat")
        }
    };

    return (
        <Wrapper>
            {state.isNewChat && 
                <Suggest>
                    {defaultPrompts.map((x, i) => {
                        return (<PillComponent 
                            id={`default_${i}`}
                            favorite={false}
                            name={x}
                            handleDelete={()=>{}}
                            handleFavouriteToggle={()=>{}}
                            handleRename={()=>{}}
                            handleClick={(id, text) => {
                                setMessage(text)
                                if (textareaRef.current) {
                                    textareaRef.current.style.height = "auto";
                                    textareaRef.current.rows = 1;
                                }
                            }}
                        ></PillComponent>)
                    })}
                    <PillComponent 
                        id='plus' 
                        name=''
                        favorite={false}
                        handleDelete={()=>{}}
                        handleFavouriteToggle={()=>{}}
                        handleRename={()=>{}}><PlusIcon/>
                    </PillComponent>
                </Suggest>}
            {!state.isNewChat && <ChatHistoryComponent></ChatHistoryComponent>}
            <ChatInputWrapper>
                <FileIcon onClick={toggleModal} style={{ cursor: "pointer" }} />
                <StyledTextarea
                    ref={textareaRef}
                    value={message}
                    onInput={handleInput}
                    onKeyDown={handleKeyDown}
                    rows={1}
                    placeholder='Ask Scout...'
                />
                <MicIcon style={{ cursor: "pointer" }} />
                <SendIcon onClick={sendMessage} style={{ cursor: "pointer" }} />
            </ChatInputWrapper>
            <Modal
                headerText={"Add files"}
                isVisible={isModalVisible}
                toggleModal={toggleModal}
                onSubmit={ () => {
                    addFilesMutation()
                }}
                width='300px'
                loading={isSaving}
            >
                <FilesArea onDrop={(x) => {
                    console.log(x)
                }} {...getRootProps({className: 'dropzone'})}>
                    <input {...getInputProps()} />
                    <Reg_12>
                        + Add files to this Knowledge Base.
                    </Reg_12>
                </FilesArea>
                <Reg_10 style={{textAlign: 'center'}}>100MB max of PDFs and DOCs per chat.</Reg_10>
                {myFiles.map(f => {
                    return (<File>
                        <Icon><AttachmentIcon /></Icon>
                        <Reg_10>{`${f.name} (${formatBytes(f.size)})`}</Reg_10>
                        <Icon onClick={() => {
                            const files = myFiles.filter(x => x.name !== f.name)
                            setMyFiles(files)
                        }}><TrashIcon /></Icon>
                        </File>)
                })}
            </Modal>
        </Wrapper>
    );
})
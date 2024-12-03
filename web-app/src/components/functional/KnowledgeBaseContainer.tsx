import styled from 'styled-components';
import { useStateContext } from '../../StateContext';
import { Reg_14, Reg_18 } from "../styling/typography"
import { useMutation, useQueries, useQuery, useQueryClient } from 'react-query';
import { Select } from "../ui/Select"
import { createKb, getPredefinedKbs, getPrivateKbs, getPublicKbs, updateKb} from "../../api/api"
import { ReactComponent as BrainIcon } from "../../assets/icons/brain.svg";
import { ReactComponent as InfoIcon } from "../../assets/icons/info-icon.svg";
import { useState } from 'react';
import { KnowledgeBaseComponent } from './KnowledgeBaseComponent';
import { useLocalStorage } from '../hooks/useLS';
import { KnowledgeBaseModel } from '../../api/model';
import { InputTextBox } from '../ui/InputTextBox';
import { IconButton, Switch, Tooltip } from "@mui/material";
import { toast } from 'react-toastify';

const Container = styled.div`
    display: grid;
    grid-template-rows: calc(100% - 42px) 2px 40px;
    width: 303px;
    height: 100%;

    &.new-kb {
        grid-template-rows: calc(100% - 85px) 2px 83px;
    }
`;

const KbContainer = styled.div`
    display: flex;
    flex-direction: column;
    width: 303px;
    height: 100%;
    overflow: hidden; /* Prevents scroll on the entire container */
`;

const Divider = styled.div`
    background-color: var(--divider)
`;

const CreateButton = styled.button`
    height: 40px;
    width: 100%;
    border-radius: 8px;
    background-color: var(--button-secondary-bg);
    color: var(--white);
    display: grid;
    grid-template-columns: 40px calc(100% - 40px);
    align-items: center;
    margin: 5px 0;
`;

const SaveButton = styled.button`
    height: 40px;
    width: 100%;
    border-radius: 8px;
    background-color: var(--button-secondary-bg);
    color: var(--white);
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 5px 0;

    &.cancel {
        background-color: var(--background);
        color: var(--button-secondary-bg);
        border: none;
    }
`;

const Center = styled.div`
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
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

const Label = styled.span`
    display: flex;
    align-items: center;
`

const Icon = styled.div`
    padding: 5px;
`

const Subtitle = styled.div`
    display: flex;
    justify-content: start;
    width: 100%;
    padding-top: 20px;
`

const KbOverflow = styled.div`
    display: flex;
    overflow-y: auto;
    flex-direction: column;
    max-height: calc(100% - 120px);
    width: 100%;
    padding-bottom: 55px;
`

const models = [
    {text: 'Gemini 1.5 - Pro', id: 'gemini-1.5-pro'},
    {text: 'Gemini 1.5 - Flash', id: 'gemini-1.5-flash'}
]

export const KnowledgeBaseContainer = () => {
    const { dispatch } = useStateContext();
    const [editionId, setEditionId] = useState("");
    const [isNew, setIsNew] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const [isPublic, setIsPublic] = useState(false);
    const [knowledgeName, setKnowledgeName] = useState('');
    const queryClient = useQueryClient()
    const { mutateAsync: addKbMutation} = useMutation({
        mutationFn: async (text: string) => {
            if(isNew) {
                const response = await createKb(text, isPublic)
                if(response.success) {
                    queryClient.invalidateQueries(["my_kb"])
                    queryClient.invalidateQueries(["other_kb"])
                    toast.success(response.message)
                }
            } else {
                const response = await updateKb(editionId, text, isPublic)
                if(response.success) {
                    queryClient.invalidateQueries(["my_kb"])
                    queryClient.invalidateQueries(["other_kb"])
                    toast.success(response.message)
                }
            }
        },
    })
    let [currentKbs, setCurrentsKbs] = useLocalStorage("kbs",[])
    const kbs = useQueries([
        {
            queryFn: () => getPrivateKbs(),
            queryKey: ["my_kb"]
        },
        {
            queryFn: () => getPublicKbs(),
            queryKey: ["other_kb"]
        },
        {
            queryFn: () => getPredefinedKbs(),
            queryKey: ["system_kb"]
        }
    ])
    let systemKbs: KnowledgeBaseModel[] = [];
    let myKbs: KnowledgeBaseModel[] = [];
    let otherKbs: KnowledgeBaseModel[] = [];
    
    if(kbs && kbs.length === 3){
        let localKbs: KnowledgeBaseModel[] = []
        myKbs = kbs[0].data ? kbs[0].data?.data.map((x: KnowledgeBaseModel) => {
            const kb = currentKbs.find((y: KnowledgeBaseModel) => y.id === x.id);
            if(kb) {
                x.active = kb.active
            } else {
                x.active = false
            }
            return x;
        }) : []
        otherKbs = kbs[1].data ? kbs[1].data?.data.map((x: KnowledgeBaseModel) => {
            const kb = currentKbs.find((y: KnowledgeBaseModel) => y.id === x.id);
            if(kb) {
                x.active = kb.active
            } else {
                x.active = false
            }
            return x;
        }) : []
        systemKbs = kbs[2].data ? kbs[2].data?.data.map((x: KnowledgeBaseModel) => {
            const kb = currentKbs.find((y: KnowledgeBaseModel) => y.id === x.id);
            if(kb) {
                x.active = kb.active
            } else {
                x.active = false
            }
            return x;
        }) : []
        localKbs = [...myKbs, ...otherKbs, ...systemKbs]
        localStorage.setItem("kbs", JSON.stringify(localKbs));
    }

    const isEditonMode = () => {
        return isNew || isEditing
    }

    const changeActiveKbInLocal = (change: string, model: KnowledgeBaseModel) => {
        if(change === "active" || change === "inactive") {
            if(currentKbs.some((x: KnowledgeBaseModel) => x.id === model.id)) {
                currentKbs = currentKbs.map((x: KnowledgeBaseModel) => {
                    if(x.id === model.id) {
                        x.active = change === "active" ? true : false;
                    }
                    return x
                })
            } else {
                currentKbs.push({...model, active: change === "active" ? true : false})
            }
            setCurrentsKbs(currentKbs)
        }
    }
    return (
        <Container className={isNew ? 'new-kb': ''}>
            {!isEditonMode() && <><KbContainer>
                <> 
                    <Reg_18>Knowledge Base</Reg_18>
                    <></>
                    <Select label='Model' 
                        value='gemini-1.5-pro' 
                        width='100%' 
                        items={models} 
                        onChange={(model: string) => {
                            dispatch({type: 'SET_MODEL', payload: model})
                        } }></Select>
                    <></>
                    <KbOverflow>
                    {systemKbs.length > 0 && <Subtitle>
                        <Reg_14>System KBs</Reg_14>
                    </Subtitle>}
                    {systemKbs.map(x => {
                        return <KnowledgeBaseComponent kbType="system" base={x} onChange={(change, model) => {
                            changeActiveKbInLocal(change, model)
                        }}></KnowledgeBaseComponent>
                    })}
                    {myKbs.length > 0 && <Subtitle>
                        <Reg_14>My KBs</Reg_14>
                    </Subtitle>}
                    {myKbs.map(x => {
                        return <KnowledgeBaseComponent 
                            kbType="mine" 
                            base={x} 
                            onEdit={(id: string, name: string, isPublic: boolean) => {
                                setIsEditing(true)
                                setKnowledgeName(name)
                                setIsPublic(isPublic)
                                setEditionId(id)
                            }}
                            onChange={(change, model) => {
                                changeActiveKbInLocal(change, model)
                            }}></KnowledgeBaseComponent>
                    })}
                    {otherKbs.length > 0 && <Subtitle>
                        <Reg_14>Public KBs</Reg_14>
                    </Subtitle>}
                    {otherKbs.map(x => {
                        return <KnowledgeBaseComponent 
                            kbType="others" 
                            base={x} 
                            onEdit={(id: string, name: string, isPublic: boolean) => {
                                setIsEditing(true)
                                setKnowledgeName(name)
                                setIsPublic(isPublic)
                                setEditionId(id)
                            }}
                            onChange={(change, model) => {
                                changeActiveKbInLocal(change, model)
                            }}></KnowledgeBaseComponent>
                    })}
                    </KbOverflow>
                </>
            </KbContainer>
            <Divider />
            <CreateButton onClick={()=>{setIsNew(true)}}>
                <Center><BrainIcon /></Center>
                <Reg_14>Create a new Knowledge Base</Reg_14>
            </CreateButton></>}
            {isEditonMode() && <>
                <KbContainer>
                    <Reg_18>New Knowledge Base</Reg_18>
                    <InputTextBox value={knowledgeName} label='Knowledge Base Name' width='100%' onChange={(x) => {setKnowledgeName(x)}}></InputTextBox>
                    <Option>
                        <Label>
                            Share with Team
                            <Tooltip title="Share this knowledge base with your team">
                                <IconButton>
                                    <InfoIcon />
                                </IconButton>
                            </Tooltip>
                        </Label>
                        <Switch
                            checked={isPublic}
                            onChange={() => {
                                setIsPublic(!isPublic)
                            }}
                            inputProps={{ "aria-label": "Share with team" }}
                        />
                    </Option>
                </KbContainer>
                <Divider />
                <Center>
                    <SaveButton onClick={() =>{
                        if(knowledgeName) {
                            addKbMutation(knowledgeName)
                            setIsNew(false)
                            setIsEditing(false)
                        } else {
                            toast.error("Knowledge base name is required")
                        }
                    }}>Save</SaveButton>
                    <SaveButton className='cancel' onClick={()=>{setIsNew(false)}}>Cancel</SaveButton>
                </Center>
            </>}
        </Container>
    );
}
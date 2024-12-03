import styled from 'styled-components';
import { useDropzone } from 'react-dropzone'
import { ReactComponent as Brain } from "../../assets/icons/brain.svg";
import { ReactComponent as IconMore } from "../../assets/icons/icon-more.svg";
import { ReactComponent as TrashIcon } from "../../assets/icons/trash.svg";
import { toast } from "react-toastify";
import { Switch } from "@mui/material";
import { KnowledgeBaseModel } from '../../api/model';
import { Reg_12, Reg_14 } from '../styling/typography';
import { useEffect, useRef, useState } from 'react';
import { FileComponent } from './FileComponent';
import Modal from "../functional/ModalComponent";
import { useMutation, useQueryClient } from 'react-query';
import { addFilesToKb, deleteFilesFromKb, deleteKb } from '../../api/api';

interface KnowledgeBaseProps {
    base: KnowledgeBaseModel;
    kbType: string;
    onChange?: (change: string, base: KnowledgeBaseModel) => void;
    onEdit?: (id: string, name: string, isPublic: boolean) => void;
}

const KnowledgeBase = styled.a`
    width: 100%;
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    text-decoration: none;
    border-width: 0.5px;
    border-style: solid;
    border-color: var(--pill-border);
    padding: 10px;
    color: var(--regular-font-color);
    margin: 10px 0;
    position: relative;
    &.active {
        background-color: var(--button-bg);
        border-color: var(--button-bg);
        color: var(--button-font)
    }
`;

const Header = styled.div`
    width: 100%;
    display: grid;
    grid-template-columns: 30px calc(100% - 80px) 45px 5px;
    align-items: center;
    cursor: pointer;
`;

const Body = styled.div`
    width: 100%;
    display: flex;
    align-items: center;
    flex-direction: column;
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

const Context = styled.div`
    position: absolute;
    background-color: var(--background);
    min-width: 160px;
    box-shadow: 0px 8px 16px 0px rgba(0, 0, 0, 0.2);
    z-index: 1;
    right: 0;
    top: 45px;
    & a {
        color: var(--font-color);
        padding: 12px 16px;
        text-decoration: none;
        display: block;
    }
`;

const Icon = styled.div`
    padding: 0 5px;
`

const DeleteBack = styled.div`
    position: absolute;
    top: 0;
    bottom: 0;
    right: 0;
    left: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: var(--file-bubble);
    color: var(--file-bubble-color);
    opacity: 0.5;
`

const Option = styled.a`
    cursor: pointer;
`

export const KnowledgeBaseComponent: React.FC<KnowledgeBaseProps> = ({ base, onChange, kbType, onEdit }) => {
    const [isOpen, setOpen] = useState(false);
    const [active, setActive] = useState(base.active);
    const [expanded, setExpanded] = useState(false);
    const [isDeleteOpen, setDeleteOpen] = useState(false);
    const queryClient = useQueryClient()
    const {acceptedFiles, getRootProps, getInputProps} = useDropzone();
    const dropdownRef = useRef<HTMLDivElement>(null)

    const { mutateAsync: addFilesMutation, isLoading} = useMutation({
        mutationFn: async () => {
            if(acceptedFiles.length){
                const response = await addFilesToKb(base.id, acceptedFiles)
                if(response.success) {
                    if(response.data?.embedding_results){
                        for (const [key, value] of Object.entries(response.data?.embedding_results)) {
                            if(value === 'success') {
                                if(kbType === 'mine'){
                                    queryClient.invalidateQueries(["my_kb"])
                                } else {
                                    queryClient.invalidateQueries(["other_kb"])
                                }
                            } else {
                                toast.error("File couldn't be indexed")
                            }
                        }
                    }
                }
            }
        },
    })

    const { mutateAsync: deleteKbMutation, isLoading: deleting} = useMutation({
        mutationFn: async () => {
            const response = await deleteKb(base.id)
            if(!response.success) {
                toast.error(response.message)
            } else {
                if(kbType === 'mine'){
                    queryClient.invalidateQueries(["my_kb"])
                } else {
                    queryClient.invalidateQueries(["other_kb"])
                }
            }
        },
    })

    const { mutateAsync: deleteFileMutation } = useMutation({
        mutationFn: async (id: string) => {
            const response = await deleteFilesFromKb(base.id, [id])
            if(!response.success) {
                toast.error(response.message)
            } else {
                if(kbType === 'mine'){
                    queryClient.invalidateQueries(["my_kb"])
                } else {
                    queryClient.invalidateQueries(["other_kb"])
                }
            }
        },
    })

    const handleClickOutside = (event: MouseEvent) => {
        if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
            setOpen(false);
        }
      };

    useEffect(() => {
        addFilesMutation()
    }, [acceptedFiles])

    useEffect(() => {
        document.addEventListener('click', handleClickOutside, true);
        return () => {
          document.removeEventListener('click', handleClickOutside, true);
        };
    }, []);

    return (
        <KnowledgeBase className={active ? 'active': ''}>
            <Header>
                <Brain onClick={()=> { setExpanded(!expanded) }} />
                <Reg_14 onClick={()=> { setExpanded(!expanded) }}>{base.name}</Reg_14>
                <></>
                <Switch
                    size="small"
                    checked={active}
                    onChange={(e) => {
                        setActive(!active)
                        if(onChange) {
                            onChange(active? 'inactive': 'active', base)
                        }
                    }}
                />
                {kbType !== 'system' && <Icon onClick={(e) => {
                    setOpen(true)
                }}>
                    <IconMore style={{textAlign: "center"}}/>
                </Icon>}
            </Header>
            {expanded && <Body>
                {kbType !== 'system' &&(<FilesArea {...getRootProps({className: 'dropzone'})}>
                    <input {...getInputProps()} />
                    <Reg_12>
                        + Add files to this Knowledge Base.
                    </Reg_12>
                </FilesArea>)}
                {base.filesIds && base.filesIds.map(f => {
                    return (<FileComponent 
                        id={f} 
                        onDelete={(id: string) => {
                            deleteFileMutation(id)
                        }} 
                        loading={false}></FileComponent>)
                })}
                {isLoading && <FileComponent id={''} loading={true}></FileComponent>}
            </Body>}
            {isOpen && (
                <Context className="" onClick={(e) => e.stopPropagation()} ref={dropdownRef}>
                    <input type='hidden' />
                    <Option onClick={()=>{
                        onEdit && onEdit(base.id, base.name, base.public)
                    }}>Edit</Option>
                    <Option onClick={() => {
                        setDeleteOpen(true)
                        }}>Delete</Option>
                </Context>
            )}
            {deleting && <DeleteBack><TrashIcon /></DeleteBack>}
            <Modal
                headerText={"Delete KB"}
                isVisible={isDeleteOpen}
                toggleModal={() => setDeleteOpen(!isDeleteOpen)}
                onSubmit={ () => {
                    deleteKbMutation()
                    setOpen(false)
                }}
            >
                <>Do you want to delete this Knowledge Base?</>
            </Modal>
        </KnowledgeBase>
    );
}
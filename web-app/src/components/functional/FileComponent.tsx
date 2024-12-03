import styled from 'styled-components';
import { ReactComponent as AttachmentIcon } from "../../assets/icons/attachment.svg";
import { ReactComponent as TrashIcon } from "../../assets/icons/trash.svg";
import { Reg_10 } from '../styling/typography';
import { useQuery } from 'react-query';
import { getFileById } from '../../api/api';
import { useState } from 'react';


const File = styled.div`
    width: 100%;
    display: grid;
    grid-template-columns: 30px calc(100% - 60px) 30px;
    align-items: center;
    background-color: var(--background);
    color: var(--font-color);
    border: none;
    border-radius: 30px;
    height: 25px;
    justify-content: center;
    margin: 10px 0;
    cursor: pointer;
    position: relative;
    &.loading {
        background: linear-gradient(-45deg, var(--background), #a0a0a0, #a0a0a0, var(--background));
        background-size: 400% 400%;
	    animation: gradient 5s ease infinite;
    }
`;

const Icon = styled.div`
    width: 100%;
    display:flex;
    justify-content: center;
`;

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


export const FileComponent= ({id, loading, onDelete}: {id: string; loading: boolean; onDelete?: Function}) => {
    const {data: fileData, isLoading} = useQuery({
        queryFn: () => {
            return id ? getFileById(id): undefined
        },
        queryKey: ["fileId", {id}]
    })
    const [deleting, setDelete] = useState(false)

    function formatBytes(bytes: number, decimals = 1) {
        if (!+bytes) return '0 Bytes'
    
        const k = 1024
        const dm = decimals < 0 ? 0 : decimals
        const sizes = ['b', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']
    
        const i = Math.floor(Math.log(bytes) / Math.log(k))
    
        return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`
    }
    
    if(fileData && fileData.data) {
        return (
            <File>
                <Icon><AttachmentIcon /></Icon>
                <Reg_10>{`${fileData.data.name} (${formatBytes(fileData.data.sizeBytes)})`}</Reg_10>
                <Icon onClick={() => {
                    if(onDelete) {
                        setDelete(true)
                        onDelete(id)
                    }
                }}><TrashIcon /></Icon>
                {deleting && <DeleteBack><TrashIcon /></DeleteBack>}
            </File>
        )
    }
    if(isLoading || loading) {
        return (
            <File className='loading'>
                <Icon><AttachmentIcon /></Icon>
                <Reg_10>Loading...</Reg_10>
                <Icon></Icon>
            </File>
        )
    }
    return <></>
}
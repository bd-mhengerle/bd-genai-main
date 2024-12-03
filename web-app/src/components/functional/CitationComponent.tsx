import styled from 'styled-components';
import { Reg_10 } from "../styling/typography"
import { useQuery } from 'react-query';
import { getSignedFile } from '../../api/api';
import { useState } from 'react';

const Citation = styled.div`
    padding: 0 10px;
    border-radius: 12px;
    height: 25px;
    max-width: 100px;
    background-color: var(--launch);
    color: var(--launch-font-color);
    white-space: nowrap;
    text-overflow: ellipsis;
    margin: 5px;
    cursor: pointer;
    overflow: hidden;
    line-height: 25px;
`

const getFileName = (path: string) => {
  return path.substring(path.lastIndexOf('/') + 1);
}

const CitationComponent = ({id}: {id: string;}) => {
  const [enabled, setEnabled] = useState(false);
  const {data: file, isLoading} = useQuery({
        queryFn: async () => {
          const signedFile = await getSignedFile(id)
          if(signedFile.success) {
            window.open(signedFile.data?.authenticatedURL, '_blank')
          }
          return signedFile
        },
        queryKey: ["signedFile", {id}],
        enabled: enabled
    })

    return (
      <Reg_10>
        <Citation 
          title={id} // Full path shown on hover
          onClick={() => {
            if(id.startsWith('http')){
              window.open(id, '_blank')
            } else {
              if(file?.success) {
                window.open(file.data?.authenticatedURL, '_blank')
              } else {
                !file && setEnabled(true)
              }
            }
          }}
        >
          {!isLoading ? getFileName(id) : 'Opening...'}
        </Citation>
      </Reg_10>
    );
}

export default CitationComponent;

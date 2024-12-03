import React, { ReactNode, useState } from 'react';
import styled from 'styled-components';
import { ReactComponent as StarIcon } from '../../assets/icons/star-icon.svg';
import { useStateContext } from '../../StateContext';
import { useNavigate } from 'react-router-dom';
import { ChatModel } from '../../api/model';
import { Reg_12 } from '../styling/typography';

const Pill = styled.p`
    min-height: 36px;
    border-radius: 30px;
    border-width: 0.5px;
    border-color: var(--pill-border);
    border-style: solid;
    display: grid;
    grid-template-columns: 35px auto 35px;
    align-items: center;
    padding: 5px 0;
    &:hover {
      background-color: var(--pill-hover);
      color: var(--background);
      cursor: pointer;
    }
`;

const Icon = styled.div`
    text-align: center;
`;


interface PillProps {
  name: string;
  id: string;
  favorite: boolean;
  handleFavouriteToggle: (index: number) => void;
  handleDelete: (index: number) => void;
  handleRename: (index: number, newText: string) => void;
  handleClick?: (id: string, text: string) => void;
  children?: ReactNode
}

export const PillComponent: React.FC<PillProps> = ({ name, id, children, favorite, handleFavouriteToggle, handleDelete, handleRename, handleClick }) => {
  const { dispatch } = useStateContext();
  const navigate = useNavigate();

  const handleEditClick = (index: number) => {

  };

  const handleEditChange = (e: React.ChangeEvent<HTMLInputElement>) => {
  };

  const handleEditSave = (index: number) => {
  };

  const handleChatClick = (query: any) => {
    console.log(query);
  };

  

  return (
    <>
      <Pill onClick={() => {
        if(handleClick) {
          handleClick(id, name)
        }
      }}>
        <Icon>{favorite && <StarIcon />}</Icon>
        {!children &&<Reg_12>{name}</Reg_12>}
        {!!children && children}
        <div>
        </div>
      </Pill> 
    </>
  );
};

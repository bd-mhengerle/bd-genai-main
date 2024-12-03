import React from 'react';
import { useStateContext } from "../../StateContext";

interface ProfileInitialsProps {
  firstName: string;
  lastName: string;
}

const ProfileInitialsComponent: React.FC<ProfileInitialsProps> = ({ firstName, lastName }) => {
  const { state, dispatch } = useStateContext();

  const getInitials = (firstName: string, lastName: string): string => {
    return `${firstName ? firstName[0]: ''}${lastName ? lastName[0] : ''}`;
  }

  return (
    <div className="profile-initials" onClick={() => {
      if(state.isRightPanelOpen && state.rightPanel !== 'profile') {
        dispatch({type: 'OPEN_PROFILE', payload: {}})
      } else {
        dispatch({type: 'TOGGLE_PROFILE', payload: {}})
      }
    }}>
      {getInitials(firstName, lastName)}
    </div>
  );
}

export default ProfileInitialsComponent;

import { ReactNode } from "react";
import { useStateContext } from "../../StateContext";
import styled from 'styled-components';

const SidePanelContainer = styled.div<{ isOpen?: boolean, position: 'left' | 'right' }>`
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
  padding: ${(props) => (props.isOpen ? '10px' : '10px')};
  box-sizing: border-box;
  background-color: ${(props) => (props.isOpen ? 'var(--background)' : 'transparent')};
  width: ${(props) => (props.isOpen ? '360px' : '0')};
  transition: width 0.3s ease, padding 0.3s ease;
  overflow: hidden;
  position: ${(props) => (props.isOpen ? 'absolute' : 'absolute')};
  right: ${(props) => (props.position === 'right' ? '0'  : '')};
  grid-row: 2;
  grid-column: ${(props) => (props.position === 'left' ? '1' : '3')};
`;

const SliderContainer = styled.div<{ isOpen?: boolean, isLeft: boolean}>`
  position: absolute;
  top: 50%;
  right: ${(props) => (props.isOpen && props.isLeft ? '0' : '')};
  left: ${(props) => (props.isOpen && !props.isLeft ? '0' : '')};
  transform: translateY(-50%);
  height: 100px;
  width: 30px;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: width 0.3s ease;
  cursor: pointer;
  
  &:hover {
    width: 30px;
  }
`;

const SliderThumb = styled.div<{isLeft: boolean}>`
  width: 5px;
  height: 50px;
  background-color: #b0b0b0;
  position: relative;
  
  ${SliderContainer}:hover &::before {
    position: absolute;
    color: #000;
    font-size: 10px;
  }
`;

const ToggleButton = ({ isOpen, onClick, isLeft } : {isOpen: boolean, onClick: () => void, isLeft: boolean}) => (
    <SliderContainer onClick={onClick} isOpen={isOpen} isLeft={isLeft}>
      <SliderThumb isLeft={isLeft}/>
    </SliderContainer>
  );

const SidePanelComponent = ({
    position,
    children,
}: {
    position: 'left' | 'right'
    children: ReactNode
}) => {
    const { state, dispatch } = useStateContext();

    return (
        <SidePanelContainer isOpen={position === 'left' ? state.isHistoryOpen : state.isRightPanelOpen} position={position}>
            {children}
            <ToggleButton isLeft={position === 'left'} isOpen={position === 'left' ? state.isHistoryOpen : state.isRightPanelOpen} onClick={() => { 
                dispatch({ type: position === 'left' ? "TOGGLE_HISTORY" : 'TOGGLE_RIGHT_PANEL', payload: null })}
            } />
        </SidePanelContainer>
    );
};

export default SidePanelComponent;

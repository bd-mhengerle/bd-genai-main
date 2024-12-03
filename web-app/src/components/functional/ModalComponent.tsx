import React, { ReactNode } from "react";
import styled from "styled-components";
import { ReactComponent as CloseIcon } from "../../assets/icons/close-icon.svg";
import { Reg_12 } from "../styling/typography";

const Container = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  z-index: 2;
  background: rgba(0, 0, 0, 0.5);
`;

const ModalContent = styled.div<{ width?: string; }>`
  background: var(--background);
  border-radius: 10px;
  padding: 20px;
  max-width: 500px;
  width: ${(props) => props.width || "100%"};
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
`;

const Title = styled.h5`
  margin: 0;
`;

const CloseButton = styled(CloseIcon)`
  cursor: pointer;
`;

const Body = styled.div`
  margin-bottom: 20px;
`;

const Footer = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: space-around;
  gap: 10px;
`;

const Button = styled.button<{ backgroundColor?: string; color?: string }>`
  padding: 10px 20px;
  background-color: ${(props) => props.backgroundColor || "#007bff"};
  color: ${(props) => props.color || "#ffffff"};
  border: none;
  border-radius: 5px;
  cursor: pointer;
`;

interface ModalProps {
  headerText: string;
  isVisible: boolean;
  toggleModal: () => void;
  children: ReactNode;
  onSubmit?: () => void;
  width?: string;
  loading?: boolean;
}

const Modal = ({
  headerText,
  isVisible,
  toggleModal,
  children,
  onSubmit,
  width,
  loading = false
}: ModalProps) => {
  if (!isVisible) return null;

  return (
    <Container>
      <ModalContent width={width}>
        <Header>
          <Title>{headerText}</Title>
          <CloseButton onClick={toggleModal} />
        </Header>
        {!loading && <Body>{children}</Body>}
        {!loading && <Footer>
          {onSubmit && (
            <Button backgroundColor="#0590C8" color="#ffffff" onClick={onSubmit}>
              Submit
            </Button>
          )}
          <Button backgroundColor="var(--background)" color="var(--font-color)" onClick={toggleModal}>
            Cancel
          </Button>
        </Footer>}
        {loading && <Reg_12>Loading...</Reg_12>}
      </ModalContent>
    </Container>
  );
};

export default Modal;
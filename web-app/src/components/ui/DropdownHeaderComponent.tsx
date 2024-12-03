import React, { useState, useEffect, useRef } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faChevronDown } from '@fortawesome/free-solid-svg-icons'

interface DropdownProps {
  details: string;
  handleRename?: () => void;
  handleShare?: () => void;
  handleFavorite?: () => void;
  handleDelete?: () => void;
  showDropdown: boolean
}

const Dropdown: React.FC<DropdownProps> = ({ details, handleRename, handleDelete, handleShare, handleFavorite, showDropdown }) => {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const toggleDropdown = () => {
    if(showDropdown){
      setIsOpen(!isOpen)
    }
  }

  const handleClickOutside = (event: MouseEvent) => {
    if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
      setIsOpen(false);
    }
  };

  useEffect(() => {
    document.addEventListener('click', handleClickOutside, true);
    return () => {
      document.removeEventListener('click', handleClickOutside, true);
    };
  }, []);

  return (
    <div className="header-dropdown" onClick={toggleDropdown} ref={dropdownRef}>
      <div className="chat-dropdown">{details}</div>
      {showDropdown && <FontAwesomeIcon icon={faChevronDown} />}
      {isOpen && (
        <div className="header-dropdown-content" onClick={(e) => e.stopPropagation()}>
          <a onClick={() => {
            handleRename && handleRename()
            }}>Rename</a>
          <a onClick={() => {
            handleFavorite && handleFavorite()
          }}>Favorite</a>
          <a onClick={() => {
            handleShare && handleShare()
          }}>Share</a>
          <a onClick={()=>{
            handleDelete && handleDelete()
            }}>Delete</a>
        </div>
      )}
    </div>
  );
};

export default Dropdown;
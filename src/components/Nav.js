import React from 'react'

const Nav = ({ nav, onHover, onClick}) => {
    return (
        <div
            className= 'nav'
            style={{color: nav.hover ? 'rgb(66, 175, 176)' : 'rgb(13, 37,70)'}}
            onMouseEnter={() => onHover(nav.id, true)} 
            onMouseLeave={() => onHover(nav.id, false)}
            onClick={() => onClick(nav.link)}
        >
            {nav.name}
        </div>
    )
}

export default Nav

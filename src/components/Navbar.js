import React from 'react'
import Nav from './Nav'

const Navbar = ({ navs, onHover, onClick }) => {
    return (
        <nav className='navbar'>
            <h2 className='nav-name'>Dylan Faelker</h2>
            <div className='nav-choice'>
                {navs.map((nav) => (
                    <Nav
                        key={nav.id} 
                        nav={nav}
                        onHover={onHover}
                        onClick={onClick}
                    />
                ))}
            </div>
            
        </nav>
    )
}

export default Navbar

import React from 'react'
import Career from './Career'
import ResumePDF from '../Resume2021.pdf'

const Careers = ({ careers }) => {
    return (
        <div className='section'>
            <header className='header'>
                <h3>Career History</h3>
            </header>

            {/* Resume */}
            <div className='section-small'>
              <a className='link-to-github' href={ResumePDF} target="_blank">Click for Resume</a>
            </div>

            {careers.map((career) => (
                <Career
                    key={career.id} 
                    career={career}
                />
            ))}
        </div>
    )
}

export default Careers

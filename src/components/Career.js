import React from 'react'

const career = ({ career }) => {
    return (
        <div className='career'>
            {career.date}
            {career.title}
            {career.location}
        </div>
    )
}

export default career

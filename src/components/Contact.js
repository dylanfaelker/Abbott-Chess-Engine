const Contact = ({ contact, onHover }) => {
    return (
        <a 
        className='contactLink'
        href={contact.link}
        target="_blank"
        rel="noopener noreferrer"
        onMouseEnter={() => onHover(contact.id, true)} 
        onMouseLeave={() => onHover(contact.id, false)}

        >
            {contact.hover ? contact.iconHighlight : contact.icon}
            {contact.writting}
        </a>
    )
}

export default Contact

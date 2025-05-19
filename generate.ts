function parseBookmarks(html: string) {
  return html.match(/(?<=A HREF=")[^"]+/g)?.map((url) => {
    const parsedUrl = new URL(url)

    return {
      site: parsedUrl.hostname,
      pathRule: parsedUrl.pathname + parsedUrl.search === '/'
        ? ''
        : `${parsedUrl.pathname}${parsedUrl.search}^`,
    }
  })
}

function parseLists(text: string) {
  return text.split('\n')
    .map((line) => line.trim())
    .filter((line) => line !== '' && !line.startsWith('!'))
}

const lists = {
  all: parseBookmarks(
    await (await fetch(
      'https://raw.githubusercontent.com/fmhy/bookmarks/refs/heads/main/fmhy_in_bookmarks.html',
    )).text(),
  ),

  starred: parseBookmarks(
    await (await fetch(
      'https://raw.githubusercontent.com/fmhy/bookmarks/refs/heads/main/fmhy_in_bookmarks_starred_only.html',
    )).text(),
  ),

  unsafe: parseLists(
    await (await fetch(
      'https://raw.githubusercontent.com/fmhy/FMHYFilterlist/refs/heads/main/sitelist.txt',
    )).text(),
  ),

  potentiallyUnsafe: parseLists(
    await (await fetch(
      'https://raw.githubusercontent.com/fmhy/FMHYFilterlist/refs/heads/main/sitelist-plus.txt',
    )).text(),
  ),
}

const header = `! name: FMHY Goggles
! description: Rerank results to boost sites on FMHY and remove potentially unsafe sites.
! public: true
! author: FMHY
! homepage https://github.com/fmhy/bookmarks
! issues https://github.com/fmhy/bookmarks/issues`

const goggle = [
  ...new Set(`${header}

${
    lists.all?.map((link) => `${link.pathRule}$boost=4,site=${link.site}`).join(
      '\n',
    )
  }
${lists.all?.map((link) => `$boost=2,site=${link.site}`).join('\n')}
${
    lists.starred?.map((link) => `${link.pathRule}$boost=5,site=${link.site}`)
      .join('\n')
  }
${lists.starred?.map((link) => `$boost=3,site=${link.site}`).join('\n')}
${lists.unsafe?.map((domain) => `$discard,site=${domain}`).join('\n')}
${
    lists.potentiallyUnsafe?.map((domain) => `$downrank=5,site=${domain}`).join(
      '\n',
    )
  }`.split('\n')),
].join('\n')

Deno.writeTextFileSync('fmhy.goggle', goggle)

console.log('Sucessfully generated goggle file.')
